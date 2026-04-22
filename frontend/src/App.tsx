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
  const { startRun, resumeRun, fetchFiles, fetchFileContent, fetchMemory } = useHarnessEngine()

  // All state comes from the Zustand store
  const messages = useHarnessStore(s => s.messages)
  const isRunning = useHarnessStore(s => s.isRunning)
  const isInterrupted = useHarnessStore(s => s.isInterrupted)
  const activeNode = useHarnessStore(s => s.activeNode)
  const healthy = useHarnessStore(s => s.healthy)
  const logs = useHarnessStore(s => s.logs)
  const memoryData = useHarnessStore(s => s.memoryData)
  const addMessage = useHarnessStore(s => s.addMessage)
  const indexMemory = useHarnessStore(s => s.indexMemory)

  // Fetch memory when tab changes to docs
  useEffect(() => {
    if (activeTab === 'docs') {
      fetchMemory()
    }
  }, [activeTab, fetchMemory])

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
        <TopBar healthy={healthy} activeTab={activeTab} onTabChange={setActiveTab} />

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
          ) : activeTab === 'docs' ? (
            <div className="flex-1 flex flex-col overflow-hidden bg-background">
              <div className="flex-1 flex overflow-hidden">
                {/* Knowledge Base Section */}
                <div className="flex-2 overflow-y-auto p-8 border-r border-ghost-border/10 bg-surface-container-lowest">
                  <div className="max-w-3xl mx-auto">
                    <div className="flex items-center justify-between mb-8">
                      <h2 className="text-2xl font-black text-on-surface tracking-tight flex items-center gap-3">
                        <span className="material-symbols-outlined text-primary">psychology</span>
                        PROJECT_MEMORY
                      </h2>
                      <button
                        onClick={() => indexMemory()}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-container-high hover:bg-primary hover:text-on-primary text-on-surface-variant text-[10px] font-bold rounded-md transition-all uppercase tracking-widest border border-outline/20"
                      >
                        <span className="material-symbols-outlined text-sm">refresh</span>
                        Re-Index Knowledge
                      </button>
                    </div>
                    {memoryData?.memory.sections.map((sec, i) => (
                      <div key={i} className="mb-8 animate-in fade-in slide-in-from-bottom-2 duration-500" style={{ animationDelay: `${i * 100}ms` }}>
                        <h3 className="text-xs font-bold text-primary uppercase tracking-widest mb-3 border-b border-primary/20 pb-1">{sec.header}</h3>
                        <div className="text-on-surface-variant text-sm leading-relaxed space-y-2 whitespace-pre-wrap font-inter">
                          {sec.content.join('\n')}
                        </div>
                      </div>
                    ))}
                    {!memoryData?.memory.sections.length && (
                      <div className="text-outline italic text-sm">No structured knowledge found in .harness/memory.md</div>
                    )}
                  </div>
                </div>

                {/* Timeline Section */}
                <div className="flex-1 overflow-y-auto p-8 bg-surface-container-low">
                  <h2 className="text-xs font-black text-outline mb-8 tracking-widest uppercase flex items-center gap-2">
                    <span className="material-symbols-outlined text-[1rem]">history</span>
                    Session_Timeline
                  </h2>
                  <div className="relative border-l-2 border-ghost-border/20 ml-2 pl-6 space-y-8">
                    {memoryData?.timeline.map((item, i) => (
                      <div key={i} className="relative">
                        <div className={`absolute -left-[31px] top-0 w-4 h-4 rounded-full border-4 border-surface-container-low ${item.type === 'Decision' ? 'bg-secondary' : 'bg-primary'}`}></div>
                        <div className="flex flex-col">
                          <span className="text-[10px] font-mono text-outline mb-1">{item.timestamp}</span>
                          <span className={`text-[11px] font-bold uppercase tracking-wider mb-2 ${item.type === 'Decision' ? 'text-secondary' : 'text-primary'}`}>{item.role} • {item.type}</span>
                          <p className="text-xs text-on-surface font-inter leading-snug">{item.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
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
        <footer className="h-7 bg-surface-container-lowest flex items-center px-4 justify-between border-t border-ghost-border/20 shrink-0 z-40">
          <div className="flex items-center gap-6">
            {/* Health & Node */}
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${healthy ? 'bg-secondary' : 'bg-error'}`}></span>
              <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-widest min-w-[80px]">
                {healthy ? (activeNode || 'Swarm_Standby') : 'BACKEND_OFFLINE'}
              </span>
            </div>

            {/* Token & Cost */}
            {useHarnessStore.getState().runtimeStats && (
              <div className="flex items-center gap-4 border-l border-ghost-border/10 pl-4">
                <span className="text-[10px] text-outline uppercase font-mono">
                  Tokens: <span className="text-secondary font-bold">{useHarnessStore.getState().runtimeStats?.usage.total_tokens.toLocaleString()}</span>
                </span>
                <span className="text-[10px] text-outline uppercase font-mono">
                  Cost: <span className="text-primary font-bold">${useHarnessStore.getState().runtimeStats?.usage.estimated_cost_usd.toFixed(4)}</span>
                </span>
              </div>
            )}

            {/* Project Progress */}
            <div className="flex items-center gap-2 border-l border-ghost-border/10 pl-4">
              <span className="text-[10px] text-outline uppercase font-mono">
                Tasks: <span className="text-on-surface font-bold">{useHarnessStore.getState().runtimeStats?.usage.total_tokens ? `${Object.keys(useHarnessStore.getState().nodeStatuses).length} Active` : '0/0'}</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* System Resources */}
            {useHarnessStore.getState().runtimeStats && (
              <div className="flex items-center gap-3 mr-2">
                <div className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[12px] text-outline">memory</span>
                  <span className="text-[10px] text-outline font-mono">{useHarnessStore.getState().runtimeStats?.system.memory_mb} MB</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[12px] text-outline">speed</span>
                  <span className="text-[10px] text-outline font-mono">{useHarnessStore.getState().runtimeStats?.system.cpu_percent}%</span>
                </div>
              </div>
            )}
            <span className="text-[10px] text-outline/30 font-mono italic">harnesscore@0.1.1</span>
          </div>
        </footer>
      </main>
    </div>
  )
}
