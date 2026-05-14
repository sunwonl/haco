import { useHarnessStore } from "../store/useHarnessStore";
import type { TabType } from "./Sidebar";

export default function TopBar({
    healthy,
    activeTab,
    onTabChange
}: {
    healthy: boolean,
    activeTab: TabType,
    onTabChange: (t: TabType) => void
}) {
    const setIsSettingsOpen = useHarnessStore(s => s.setIsSettingsOpen)
    const setIsConsoleOpen = useHarnessStore(s => s.setIsConsoleOpen)

    return (
        <header className="w-full h-14 bg-surface-container-low border-b border-ghost-border/15 flex justify-between items-center px-6 font-inter tracking-tight text-sm shrink-0 z-20 shadow-sm relative">
            <div className="flex items-center gap-8 h-full">
                <span className="text-lg font-black tracking-tighter text-on-surface">HARNESS_CORE</span>
                <nav className="flex items-center gap-6 h-full">
                    <div
                        onClick={() => onTabChange('workspace')}
                        className={`text-[0.8125rem] font-bold tracking-widest uppercase flex items-center gap-2 h-full cursor-pointer mt-0.5 border-b-2 transition-all ${activeTab === 'workspace' ? 'text-on-surface border-primary' : 'text-on-surface-variant border-transparent hover:text-on-surface'
                            }`}>
                        Swarm
                    </div>
                    <div
                        onClick={() => onTabChange('docs')}
                        className={`text-[0.8125rem] font-bold tracking-widest uppercase flex items-center gap-2 h-full cursor-pointer mt-0.5 border-b-2 transition-all ${activeTab === 'docs' ? 'text-on-surface border-primary' : 'text-on-surface-variant border-transparent hover:text-on-surface'
                            }`}>
                        Memory
                    </div>
                </nav>
            </div>

            <div className="flex items-center gap-3">
                {/* Live health badge */}
                <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full border shadow-inner ${healthy
                    ? 'bg-secondary/5 border-secondary/20'
                    : 'bg-error/5 border-error/20'
                    }`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${healthy ? 'bg-secondary shadow-[0_0_8px_rgba(78,222,163,0.8)]' : 'bg-error shadow-[0_0_8px_rgba(255,180,171,0.8)]'} ${healthy ? 'animate-pulse' : ''}`}></span>
                    <span className={`font-mono tracking-wider text-[9px] font-bold uppercase ${healthy ? 'text-secondary' : 'text-error'}`}>
                        {healthy ? 'HEALTHY' : 'OFFLINE'}
                    </span>
                </div>

                <div className="flex items-center gap-1">
                    <button 
                        onClick={() => setIsSettingsOpen(true)}
                        className="material-symbols-outlined text-outline hover:bg-surface-container-highest p-1 rounded transition-colors cursor-pointer text-[1.125rem]"
                        title="Settings"
                    >
                        settings
                    </button>
                    <button 
                        onClick={() => setIsConsoleOpen(true)}
                        className="material-symbols-outlined text-outline hover:bg-surface-container-highest p-1 rounded transition-colors cursor-pointer text-[1.125rem]"
                        title="Console"
                    >
                        terminal
                    </button>
                </div>
            </div>
        </header>
    )
}
