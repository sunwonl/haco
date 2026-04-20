import { useState, useCallback, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import type { TabType } from './components/Sidebar'
import LogPanel from './components/LogPanel'
import TopBar from './components/TopBar'
import ChatWorkspace from './components/ChatWorkspace'
import FileExplorer from './components/FileExplorer'
import { useHarnessStore } from './store/useHarnessStore'
import { useHarnessEngine } from './hooks/useHarnessEngine'

export default function App() {
  const [activeTab, setActiveTab] = useState<TabType>('workspace')
  const [prompt, setPrompt] = useState('')
  const [rightPanelWidth, setRightPanelWidth] = useState(450)
  const [isResizing, setIsResizing] = useState(false)

  // Engine initialises side effects (health checks, file load)
  const { startRun, resumeRun, fetchFiles, fetchFileContent } = useHarnessEngine()

  // All state comes from the Zustand store
  const messages = useHarnessStore(s => s.messages)
  const isRunning = useHarnessStore(s => s.isRunning)
  const isInterrupted = useHarnessStore(s => s.isInterrupted)
  const activeNode = useHarnessStore(s => s.activeNode)
  const healthy = useHarnessStore(s => s.healthy)
  const logs = useHarnessStore(s => s.logs)
  const addMessage = useHarnessStore(s => s.addMessage)

  const handleRun = async () => {
    if (!prompt.trim() || isRunning) return

    if (isInterrupted) {
      addMessage({ id: `user-${Date.now()}`, role: 'user', category: 'Message', text: prompt })
      handleResume(prompt)
      setPrompt('')
      return
    }

    addMessage({ id: `user-${Date.now()}`, role: 'user', category: 'Message', text: prompt })
    await startRun(prompt)
    setPrompt('')
  }

  const handleResume = (feedback?: string) => {
    resumeRun(feedback)
  }

  // Handle Resizing
  const startResizing = useCallback(() => setIsResizing(true), [])
  const stopResizing = useCallback(() => setIsResizing(false), [])
  const resize = useCallback((e: MouseEvent) => {
    if (isResizing) {
      const newWidth = window.innerWidth - e.clientX
      if (newWidth > 320 && newWidth < window.innerWidth * 0.6) {
        setRightPanelWidth(newWidth)
      }
    }
  }, [isResizing])

  useEffect(() => {
    window.addEventListener('mousemove', resize)
    window.addEventListener('mouseup', stopResizing)
    return () => {
      window.removeEventListener('mousemove', resize)
      window.removeEventListener('mouseup', stopResizing)
    }
  }, [resize, stopResizing])

  return (
    <div className={`flex h-screen w-screen overflow-hidden bg-background text-on-surface font-inter ${isResizing ? 'cursor-col-resize select-none' : ''}`}>
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="flex flex-col flex-1 pl-16 h-full">
        <TopBar healthy={healthy} />

        <section className="flex flex-1 overflow-hidden relative">
          {activeTab === 'workspace' ? (
            <>
              {/* Left Column: File Explorer (Fixed) */}
              <FileExplorer onFetchFiles={fetchFiles} onFetchContent={fetchFileContent} />

              {/* Middle Column: Chat Workspace */}
              <div className="flex-1 min-w-0 relative flex flex-col h-full">
                <ChatWorkspace
                  messages={messages}
                  isRunning={isRunning}
                  prompt={prompt}
                  setPrompt={setPrompt}
                  handleRun={handleRun}
                  isInterrupted={isInterrupted}
                  resumeRun={handleResume}
                  activeNode={activeNode}
                />
              </div>

              {/* Resizer Handle */}
              <div
                className={`w-1.5 h-full cursor-col-resize hover:bg-primary/40 transition-colors z-50 absolute right-[var(--panel-width)] -mr-0.75 top-0 bottom-0`}
                style={{ right: rightPanelWidth - 3 }}
                onMouseDown={startResizing}
              />

              {/* Right Column: Code Editor / Log Panel / Graph */}
              <div className="shrink-0 flex flex-col overflow-hidden" style={{ width: rightPanelWidth }}>
                <LogPanel logs={logs} />
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center bg-surface-container-low">
              <span className="material-symbols-outlined text-[4rem] text-outline/30 mb-4">construction</span>
              <h2 className="text-xl font-bold text-on-surface uppercase tracking-widest">{activeTab} View</h2>
              <p className="text-sm text-outline font-mono mt-2">This feature is currently under construction.</p>
              <button
                onClick={() => setActiveTab('workspace')}
                className="mt-8 px-6 py-2 bg-primary text-on-primary rounded-lg font-bold text-xs shadow-lg hover:scale-105 transition-transform"
              >
                RETURN TO WORKSPACE
              </button>
            </div>
          )}
        </section>

        {/* System Status Bar */}
        <footer className="h-6 bg-surface-container-lowest flex items-center px-4 justify-between border-t border-ghost-border/20 shrink-0 z-40">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${healthy ? 'bg-secondary' : 'bg-error'}`}></span>
              <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-widest">
                {healthy ? 'SYSTEM_READY' : 'BACKEND_OFFLINE'}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-outline">AI_Swarm: <span className="text-primary font-mono bg-primary/10 px-1 rounded">6_ACTIVE</span></span>
          </div>
        </footer>
      </main>
    </div>
  )
}
