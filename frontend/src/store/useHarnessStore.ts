import { create } from 'zustand'

export type MessageRole = 'user' | 'assistant'
export type MessageCategory = 'Thought' | 'Message' | 'ToolAction' | 'Interrupt' | 'System'

export interface ChatMessage {
    id: string
    role: MessageRole
    category: MessageCategory
    agent?: string
    text: string
    intent?: string
}

export interface LogEntry {
    type: 'node_update' | 'interrupt' | 'finish' | 'error'
    node?: string
    next_agent?: string
    next_node?: string
    logs?: any[]
    message?: string
}

export interface FileEntry {
    name: string
    path: string
    type: 'directory' | 'file'
    size?: number | null
}

interface HarnessState {
    // Session
    threadId: string | null
    setThreadId: (id: string) => void

    // Cluster health
    healthy: boolean
    setHealthy: (v: boolean) => void

    // Chat messages (middle column)
    messages: ChatMessage[]
    addMessage: (msg: ChatMessage) => void
    clearMessages: () => void

    // Agent status & Graph
    activeNode: string | null
    nodeStatuses: Record<string, 'idle' | 'thinking' | 'success' | 'error'>
    nodeDetails: Record<string, string>
    routingEdge: { from: string; to: string } | null
    isRunning: boolean
    isInterrupted: boolean
    nextNode: string | null
    setAgentStatus: (node: string | null, running: boolean, interrupted: boolean, nextNode: string | null) => void
    updateNodeStatus: (node: string, status: 'idle' | 'thinking' | 'success' | 'error') => void
    setRouting: (from: string, to: string | null) => void

    // Raw logs (right column)
    logs: LogEntry[]
    addLog: (log: LogEntry) => void
    clearLogs: () => void

    // File explorer (left column)
    files: FileEntry[]
    currentFilePath: string
    fileContent: string | null
    fileChanges: string[] // List of modified files in the current run
    setFiles: (files: FileEntry[], path: string) => void
    setFileContent: (content: string | null) => void

    // Process an SSE payload and fan it out to messages/logs/status
    dispatchSSE: (raw: any) => void
}

let _msgCounter = 0
const mkId = () => `msg-${++_msgCounter}-${Date.now()}`

export const useHarnessStore = create<HarnessState>((set, get) => ({
    threadId: null,
    setThreadId: (id) => set({ threadId: id }),

    healthy: false,
    setHealthy: (v) => set({ healthy: v }),

    messages: [],
    addMessage: (msg) => set(s => ({ messages: [...s.messages, msg] })),
    clearMessages: () => set({ messages: [] }),

    activeNode: null,
    nodeStatuses: {},
    nodeDetails: {},
    routingEdge: null,
    isRunning: false,
    isInterrupted: false,
    nextNode: null,
    setAgentStatus: (node, running, interrupted, nextNode) =>
        set({ activeNode: node, isRunning: running, isInterrupted: interrupted, nextNode }),

    updateNodeStatus: (node, status) =>
        set(s => ({ nodeStatuses: { ...s.nodeStatuses, [node]: status } })),

    setRouting: (from, to) =>
        set({ routingEdge: to ? { from, to } : null }),

    logs: [],
    addLog: (log) => set(s => ({ logs: [...s.logs, log] })),
    clearLogs: () => set({ logs: [] }),

    files: [],
    currentFilePath: '.',
    fileContent: null,
    fileChanges: [],
    setFiles: (files, path) => set({ files, currentFilePath: path }),
    setFileContent: (content) => set({ fileContent: content }),

    // The central SSE dispatcher: parse backend payloads and route them to the correct state slices
    dispatchSSE: (raw: any) => {
        const { addMessage, addLog, setAgentStatus, updateNodeStatus, setRouting } = get()

        if (raw.type === 'finish') {
            setAgentStatus(null, false, false, null)
            set({ nodeStatuses: {}, routingEdge: null })
            addLog({ type: 'finish' })
            return
        }

        if (raw.type === 'error') {
            setAgentStatus(null, false, false, null)
            addLog({ type: 'error', message: raw.message || raw.code || 'Unknown error' })
            addMessage({ id: mkId(), role: 'assistant', category: 'System', text: `❌ Error: ${raw.message || raw.code}` })
            return
        }

        if (raw.type === 'interrupt') {
            setAgentStatus(null, false, true, raw.next_node ?? null)
            addLog({ type: 'interrupt', next_node: raw.next_node })
            addMessage({
                id: mkId(), role: 'assistant', category: 'Interrupt',
                text: `⏸ Pipeline paused. Waiting for your approval to run **${raw.next_node}**.`
            })
            return
        }

        if (raw.type === 'node_update') {
            const node = raw.node ?? ''
            const status = (raw.status as any) || 'thinking'
            const nextAgent = raw.next_agent ?? null
            const incomingChanges = raw.file_changes ?? []

            // Update status and active node
            if (status === 'thinking') {
                setAgentStatus(node, true, false, null)
                updateNodeStatus(node, 'thinking')
                // Clear routing edge once thinking starts
                setRouting('', null)
            } else if (status === 'success') {
                updateNodeStatus(node, 'success')

                // Update last known details for the node from logs
                const lastLog = raw.logs?.[raw.logs.length - 1];
                if (lastLog?.details) {
                    set(s => ({ nodeDetails: { ...s.nodeDetails, [node]: lastLog.details } }));
                }

                if (nextAgent && nextAgent !== 'FINISH' && nextAgent !== 'HUMAN') {
                    setRouting(node, nextAgent)
                }

                // Handle File Changes & AutoFocus
                if (incomingChanges.length > 0) {
                    set(s => {
                        const newChanges = Array.from(new Set([...s.fileChanges, ...incomingChanges]));
                        return {
                            fileChanges: newChanges,
                            // AutoFocus: Set the current file path to the most recently changed file
                            currentFilePath: incomingChanges[incomingChanges.length - 1]
                        };
                    });
                }
            }

            addLog({ type: 'node_update', node, next_agent: raw.next_agent, logs: raw.logs, file_changes: incomingChanges })

            // Fan log entries out to chat messages
            const entries: any[] = raw.logs ?? []
            for (const entry of entries) {
                const text: string = entry.details ?? ''
                if (!text.trim()) continue

                const actionType: string = entry.action_type ?? ''
                const agentName: string = entry.agent_name ?? node

                // Map action_types to message categories
                let category: MessageCategory = 'Message'
                if (actionType === 'THOUGHT' || actionType === 'Thought') category = 'Thought'
                else if (actionType === 'TOOL_RESULT' || actionType === 'Result') category = 'ToolAction'
                else if (actionType === 'MESSAGE' || actionType === 'ORCHEST' || actionType.startsWith('ORCHEST')) category = 'Message'

                addMessage({
                    id: mkId(),
                    role: 'assistant',
                    category,
                    agent: agentName,
                    text,
                    intent: actionType,
                })
            }
        }
    },
}))
