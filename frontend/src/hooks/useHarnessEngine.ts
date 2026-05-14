import { useRef, useEffect } from 'react'
import { useHarnessStore } from '../store/useHarnessStore'

const BASE = import.meta.env.VITE_API_URL ?? ''

export function useHarnessEngine() {
    const esRef = useRef<EventSource | null>(null)
    const store = useHarnessStore()

    // Health polling: ping every 5s to update CLUSTER_HEALTHY badge
    useEffect(() => {
        const check = async () => {
            try {
                const r = await fetch(`${BASE}/api/health`)
                store.setHealthy(r.ok)
            } catch {
                store.setHealthy(false)
            }
        }
        check()
        const interval = setInterval(check, 5000)
        return () => clearInterval(interval)
    }, [])

    // Load initial file tree from CWD
    useEffect(() => {
        fetchFiles('.')
    }, [])

    const bindEventSource = (esUrl: string) => {
        if (esRef.current) esRef.current.close()
        const es = new EventSource(esUrl)
        esRef.current = es

        es.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data)
                store.dispatchSSE(data)
                if (data.type === 'finish' || data.type === 'interrupt' || data.type === 'error') {
                    es.close()
                }
            } catch {
                // ignore malformed frames
            }
        }

        es.onerror = (err) => {
            console.warn('SSE error/disconnect', err)
        }
    }

    const startRun = async (prompt: string) => {
        store.clearLogs()
        store.setAgentStatus('PO', true, false, null)

        try {
            const res = await fetch(`${BASE}/api/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, thread_id: store.threadId }),
            })
            const data = await res.json()
            const newThreadId = data.thread_id
            store.setThreadId(newThreadId)
            const enc = encodeURIComponent(prompt)
            bindEventSource(`${BASE}/api/stream/${newThreadId}?prompt=${enc}&resume=false`)
        } catch (e) {
            store.dispatchSSE({ type: 'error', message: `Failed to reach backend: ${e}` })
        }
    }

    const resumeRun = async (feedback?: any) => {
        if (!store.threadId) return

        // Ensure feedback is a string (prevent [object Object])
        const feedbackStr = (typeof feedback === 'string') ? feedback : '';

        store.setAgentStatus(store.nextNode ?? 'PO', true, false, null)
        bindEventSource(
            `${BASE}/api/interrupt/${store.threadId}${feedbackStr ? `?feedback=${encodeURIComponent(feedbackStr)}` : ''}`
        )
    }

    const fetchFiles = async (path: string = '.') => {
        store.setIsLoadingFiles(true)
        try {
            const res = await fetch(`${BASE}/api/files?path=${encodeURIComponent(path)}`)
            if (!res.ok) {
                store.setIsLoadingFiles(false)
                return
            }
            const data = await res.json()
            store.setFiles(data.entries, data.path)
        } catch {
            store.setIsLoadingFiles(false)
        }
    }

    const fetchFileContent = async (path: string) => {
        try {
            const res = await fetch(`${BASE}/api/files/content?path=${encodeURIComponent(path)}`)
            if (!res.ok) { store.setFileContent(null); return }
            const data = await res.json()
            store.setFileContent(data.content)
        } catch { store.setFileContent(null) }
    }

    const restoreState = async (threadId: string) => {
        try {
            const res = await fetch(`${BASE}/api/state/${threadId}`)
            if (!res.ok) return
            // Future: map history back to messages
        } catch { /* ignore */ }
    }

    const fetchMemory = async () => {
        try {
            const res = await fetch(`${BASE}/api/memory`)
            if (!res.ok) return
            const data = await res.json()
            store.setMemoryData(data)
        } catch { /* ignore */ }
    }

    const fetchRuntimeStats = async () => {
        if (!store.threadId) return
        try {
            const res = await fetch(`${BASE}/api/runtime/${store.threadId}`)
            if (!res.ok) return
            const data = await res.json()
            store.setRuntimeStats(data)
        } catch { /* ignore */ }
    }

    // Runtime polling: every 3s when thread exists
    useEffect(() => {
        if (!store.threadId) return
        fetchRuntimeStats()
        const interval = setInterval(fetchRuntimeStats, 3000)
        return () => clearInterval(interval)
    }, [store.threadId])

    useEffect(() => {
        return () => { if (esRef.current) esRef.current.close() }
    }, [])

    return {
        // expose only what the components need via store selectors
        startRun,
        resumeRun,
        fetchFiles,
        fetchFileContent,
        restoreState,
        fetchMemory,
    }
}
