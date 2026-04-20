export default function TopBar({ healthy }: { healthy: boolean }) {
    return (
        <header className="w-full h-14 bg-surface-container-low border-b border-ghost-border/15 flex justify-between items-center px-6 font-inter tracking-tight text-sm shrink-0 z-20 shadow-sm relative">
            <div className="flex items-center gap-8 h-full">
                <span className="text-lg font-black tracking-tighter text-on-surface">HARNESS_CORE</span>
                <nav className="flex items-center gap-6 h-full">
                    <div className="text-on-surface text-[0.8125rem] font-bold tracking-widest uppercase flex items-center gap-2 border-b-2 border-primary h-full cursor-pointer mt-0.5">
                        Swarm
                    </div>
                    <div className="text-on-surface-variant text-[0.8125rem] font-bold tracking-widest uppercase hover:text-on-surface transition-colors cursor-pointer h-full flex items-center border-b-2 border-transparent mt-0.5">
                        Runtime
                    </div>
                    <div className="text-on-surface-variant text-[0.8125rem] font-bold tracking-widest uppercase hover:text-on-surface transition-colors cursor-pointer h-full flex items-center border-b-2 border-transparent mt-0.5">
                        Memory
                    </div>
                </nav>
            </div>

            <div className="flex items-center gap-6">
                {/* Live health badge */}
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full border shadow-inner ${healthy
                        ? 'bg-secondary/5 border-secondary/20'
                        : 'bg-error/5 border-error/20'
                    }`}>
                    <span className={`w-2 h-2 rounded-full ${healthy ? 'bg-secondary shadow-[0_0_8px_rgba(78,222,163,0.8)]' : 'bg-error shadow-[0_0_8px_rgba(255,180,171,0.8)]'} ${healthy ? 'animate-pulse' : ''}`}></span>
                    <span className={`font-mono tracking-wider text-[10px] font-bold uppercase ${healthy ? 'text-secondary' : 'text-error'}`}>
                        {healthy ? 'CLUSTER_HEALTHY' : 'BACKEND_OFFLINE'}
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-outline hover:bg-surface-container-highest p-1 rounded transition-colors cursor-pointer">settings</span>
                    <span className="material-symbols-outlined text-outline hover:bg-surface-container-highest p-1 rounded transition-colors cursor-pointer">terminal</span>
                </div>

                <button className="btn-primary px-4 py-1.5 text-on-primary font-bold rounded-md active:scale-95 duration-100 flex items-center text-xs tracking-widest gap-1">
                    <span className="material-symbols-outlined text-sm">rocket_launch</span>DEPLOY
                </button>
            </div>
        </header>
    )
}
