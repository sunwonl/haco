import { useState } from 'react'
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
    addMessage({ id: `user-${Date.now()}`, role: 'user', category: 'Message', text: prompt })
    await startRun(prompt)
    setPrompt('')
  }

  const handleResume = (feedback?: string) => {
    resumeRun(feedback)
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-on-surface font-inter">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="flex flex-col flex-1 pl-16 h-full">
        <TopBar healthy={healthy} />

        <section className="flex flex-1 overflow-hidden">
          {/* Left Column: File Explorer */}
          <FileExplorer onFetchFiles={fetchFiles} onFetchContent={fetchFileContent} />

          {/* Middle Column: AI Chat Workspace */}
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

          {/* Right Column: Code Editor / Log Panel */}
          <LogPanel logs={logs} />
        </section>

        {/* System Status Bar */}
        <footer className="h-6 bg-surface-container-lowest flex items-center px-4 justify-between border-t border-ghost-border/20 shrink-0">
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
