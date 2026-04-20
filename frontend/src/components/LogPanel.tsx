import { useEffect, useRef } from 'react';

export default function LogPanel({ logs }: { logs: any[] }) {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="flex-1 bg-surface-container-lowest flex flex-col relative z-20 shrink-0 min-w-[380px]">
            {/* Editor Tabs */}
            <div className="h-10 bg-surface-container-low flex items-center px-4 gap-4 border-b border-ghost-border/15 shrink-0">
                <div className="h-full border-t-[3px] border-primary bg-surface-container-lowest px-4 flex items-center gap-2 -mb-[1px]">
                    <span className="material-symbols-outlined text-primary text-[1rem]">terminal</span>
                    <span className="text-xs font-bold tracking-widest uppercase text-on-surface">Execution Logs</span>
                    <span className="material-symbols-outlined text-[14px] text-outline hover:text-on-surface cursor-pointer ml-2">close</span>
                </div>
                <div className="h-full px-4 flex items-center gap-2 text-on-surface-variant opacity-60 hover:opacity-100 transition-opacity cursor-pointer">
                    <span className="material-symbols-outlined text-[1rem]">account_tree</span>
                    <span className="text-xs font-bold tracking-widest uppercase">State Graph</span>
                </div>
                <div className="ml-auto flex items-center gap-3">
                    <span className="px-2 py-0.5 bg-secondary/10 text-secondary text-[10px] font-bold rounded border border-secondary/20 uppercase tracking-widest">Live</span>
                    <span className="material-symbols-outlined text-outline hover:text-on-surface cursor-pointer text-[1.125rem]">more_vert</span>
                </div>
            </div>

            {/* Code Content / Logs */}
            <div className="flex-1 overflow-y-auto font-mono text-[13px] leading-6 flex bg-surface-container-lowest" ref={scrollRef}>
                {/* Line Numbers Fake (Aesthetic) */}
                <div className="w-12 bg-surface-container-low/30 text-right pr-3 py-4 select-none border-r border-outline-variant/10 shrink-0">
                    <div className="text-outline/40 text-[11px] leading-6">1</div>
                    {logs.map((_, i) => (
                        <div key={i} className="text-[11px] leading-6 max-h-none h-fit" style={{
                            /* Approximation of line counts based on log density, simplifies DOM */
                            paddingBottom: '2.5rem'
                        }}>{i + 2}</div>
                    ))}
                </div>

                {/* Actual Logs */}
                <div className="flex-1 p-4 space-y-6">
                    {logs.length === 0 && <div className="text-outline font-mono text-sm">Waiting for incoming orchestrator events...</div>}

                    {logs.map((log, i) => (
                        <div key={i} className="text-[13px]">
                            {log.type === 'error' ? (
                                <div className="bg-error/10 border-l-2 border-error/50 pl-3 py-2">
                                    <div className="text-error font-bold tracking-wide uppercase mb-1">Exception Detected</div>
                                    <div className="text-error font-mono">{log.data}</div>
                                    <div className="text-on-surface-variant text-[11px] mt-2 font-mono whitespace-pre-wrap">{log.message}</div>
                                </div>
                            ) : log.type === 'interrupt' ? (
                                <div className="bg-secondary/10 border-l-2 border-secondary/50 pl-3 py-2">
                                    <div className="text-secondary font-bold tracking-widest uppercase mb-1 flex items-center gap-2">
                                        <span className="material-symbols-outlined text-[1rem]">front_hand</span> Human Interrupt
                                    </div>
                                    <div className="text-on-surface-variant text-[12px] font-mono mt-1">Pending Approval for: {log.next_node}</div>
                                </div>
                            ) : (
                                <div className="bg-surface-container/30 border border-ghost-border/10 rounded-md p-3 shadow-sm hover:border-ghost-border/30 transition-colors">
                                    <div className="flex items-center gap-2 mb-2 border-b border-ghost-border/10 pb-2">
                                        <div className="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(137,206,255,0.8)]"></div>
                                        <div className="text-primary font-bold tracking-wider uppercase text-[10px]">Node Exec: {log.node}</div>
                                    </div>

                                    {log.logs?.map((l: any, j: number) => (
                                        <div key={j} className="text-on-surface-variant text-[12px] font-mono whitespace-pre-wrap mb-2 pl-2 border-l border-ghost-border/10">
                                            <span className="text-outline/50 select-none mr-2">{'>'}</span>{l.details}
                                        </div>
                                    ))}

                                    {log.next_agent && (
                                        <div className="flex items-center gap-2 mt-4 pt-2">
                                            <span className="text-[10px] uppercase text-outline font-bold tracking-widest">Routing</span>
                                            <span className="material-symbols-outlined text-outline text-[14px]">arrow_right_alt</span>
                                            <span className="text-[10px] text-primary bg-primary/10 px-2 py-0.5 rounded font-mono border border-primary/20">{log.next_agent}</span>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Editor Footer */}
            <div className="h-6 bg-surface-container-low flex items-center px-4 justify-between shrink-0 border-t border-ghost-border/10">
                <div className="flex items-center gap-4 text-[10px] text-outline uppercase font-mono tracking-widest">
                    <div className="flex items-center gap-1"><span className="material-symbols-outlined text-[12px]">code_blocks</span> UTF-8</div>
                    <div className="flex items-center gap-1"><span className="material-symbols-outlined text-[12px]">terminal</span> Shell Output</div>
                </div>
                <div className="text-[10px] text-outline font-mono">Lines: {logs.length}</div>
            </div>
        </div>
    )
}
