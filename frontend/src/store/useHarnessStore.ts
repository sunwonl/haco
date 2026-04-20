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

    // Agent status
    activeNode: string | null
    isRunning: boolean
    isInterrupted: boolean
    nextNode: string | null
    setAgentStatus: (node: string | null, running: boolean, interrupted: boolean, nextNode: string | null) => void

    // Raw logs (right column)
    logs: LogEntry[]
    addLog: (log: LogEntry) => void
    clearLogs: () => void

    // File explorer (left column)
    files: FileEntry[]
    currentFilePath: string
    fileContent: string | null
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
    isRunning: false,
    isInterrupted: false,
    nextNode: null,
    setAgentStatus: (node, running, interrupted, nextNode) =>
        set({ activeNode: node, isRunning: running, isInterrupted: interrupted, nextNode }),

    logs: [],
    addLog: (log) => set(s => ({ logs: [...s.logs, log] })),
    clearLogs: () => set({ logs: [] }),

    files: [],
    currentFilePath: '.',
    fileContent: null,
    setFiles: (files, path) => set({ files, currentFilePath: path }),
    setFileContent: (content) => set({ fileContent: content }),

    // The central SSE dispatcher: parse backend payloads and route them to the correct state slices
    dispatchSSE: (raw: any) => {
        const { addMessage, addLog, setAgentStatus } = get()

        if (raw.type === 'finish') {
            setAgentStatus(null, false, false, null)
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
            setAgentStatus(node, true, false, null)
            addLog({ type: 'node_update', node, next_agent: raw.next_agent, logs: raw.logs })

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
