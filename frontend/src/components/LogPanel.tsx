import { useEffect, useRef, useState } from 'react';
import GraphCanvas from './GraphCanvas';
import { useHarnessStore } from '../store/useHarnessStore';
import { useHarnessEngine } from '../hooks/useHarnessEngine';

export default function LogPanel({ logs }: { logs: any[] }) {
    const [activeSubTab, setActiveSubTab] = useState<'logs' | 'graph' | 'changes'>('logs');
    const scrollRef = useRef<HTMLDivElement>(null);
    const fileChanges = useHarnessStore(s => s.fileChanges);
    const { fetchFileContent } = useHarnessEngine();

    useEffect(() => {
        if (scrollRef.current && activeSubTab === 'logs') {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs, activeSubTab]);

    return (
        <div className="flex-1 bg-surface-container-lowest flex flex-col relative z-20 shrink-0 min-w-0 h-full">
            {/* Editor Tabs */}
            <div className="h-9 bg-surface-container-low flex items-center px-2 gap-0.5 border-b border-ghost-border/15 shrink-0 overflow-x-auto no-scrollbar">
                <button
                    onClick={() => setActiveSubTab('logs')}
                    className={`h-full px-2 flex items-center transition-all cursor-pointer shrink-0 ${activeSubTab === 'logs'
                        ? 'border-t-[2px] border-primary bg-surface-container-lowest -mb-[1px]'
                        : 'text-on-surface-variant opacity-60 hover:opacity-100'
                        }`}
                >
                    <span className={`text-[9px] font-bold tracking-widest uppercase ${activeSubTab === 'logs' ? 'text-on-surface' : ''}`}>Logs</span>
                </button>

                <button
                    onClick={() => setActiveSubTab('graph')}
                    className={`h-full px-2 flex items-center transition-all cursor-pointer shrink-0 ${activeSubTab === 'graph'
                        ? 'border-t-[2px] border-primary bg-surface-container-lowest -mb-[1px]'
                        : 'text-on-surface-variant opacity-60 hover:opacity-100'
                        }`}
                >
                    <span className={`text-[9px] font-bold tracking-widest uppercase ${activeSubTab === 'graph' ? 'text-on-surface' : ''}`}>Graph</span>
                </button>

                <button
                    onClick={() => setActiveSubTab('changes')}
                    className={`h-full px-2 flex items-center transition-all cursor-pointer shrink-0 ${activeSubTab === 'changes'
                        ? 'border-t-[2px] border-primary bg-surface-container-lowest -mb-[1px]'
                        : 'text-on-surface-variant opacity-60 hover:opacity-100'
                        }`}
                >
                    <span className={`text-[9px] font-bold tracking-widest uppercase ${activeSubTab === 'changes' ? 'text-on-surface' : ''}`}>Diff</span>
                    {fileChanges.length > 0 && (
                        <span className="bg-primary text-on-primary text-[8px] px-1 rounded-full min-w-[12px] text-center font-bold ml-1">{fileChanges.length}</span>
                    )}
                </button>

                <div className="ml-auto flex items-center gap-1 shrink-0 pl-1">
                    <span className="material-symbols-outlined text-outline hover:text-on-surface cursor-pointer text-[1rem]">more_vert</span>
                </div>
            </div>

            {/* Sub-Panel Content */}
            <div className="flex-1 overflow-hidden relative bg-surface-container-lowest">
                {activeSubTab === 'logs' ? (
                    <div className="absolute inset-0 overflow-y-auto font-mono text-[13px] flex" ref={scrollRef}>
                        {/* Line Numbers Aesthetic */}
                        <div className="w-10 bg-surface-container-low/30 text-right pr-2 py-4 select-none border-r border-outline-variant/10 shrink-0">
                            <div className="text-outline/40 text-[10px] leading-6">1</div>
                            {logs.map((_, i) => (
                                <div key={i} className="text-[10px] leading-6 py-4">{i + 2}</div>
                            ))}
                        </div>

                        {/* Actual Logs */}
                        <div className="flex-1 p-4 space-y-4">
                            {logs.length === 0 && <div className="text-outline font-mono text-sm opacity-50 italic px-2">Waiting for orchestrator events...</div>}
                            {logs.map((log, i) => (
                                <div key={i} className="animate-in fade-in slide-in-from-left-1 duration-300">
                                    {log.type === 'error' ? (
                                        <div className="bg-error/10 border-l-2 border-error/50 pl-3 py-2 rounded-r">
                                            <div className="text-error font-bold tracking-wide uppercase text-[10px] mb-1">Exception Detected</div>
                                            <div className="text-error font-mono text-[12px]">{log.data}</div>
                                            <div className="text-on-surface-variant text-[11px] mt-1 font-mono whitespace-pre-wrap">{log.message}</div>
                                        </div>
                                    ) : log.type === 'interrupt' ? (
                                        <div className="bg-secondary/15 border-l-4 border-secondary pl-4 py-3 rounded-r-lg shadow-md animate-pulse">
                                            <div className="text-secondary font-black tracking-widest uppercase text-[10px] mb-1.5 flex items-center gap-2">
                                                <span className="material-symbols-outlined text-[1.125rem]" data-weight="fill">front_hand</span>
                                                HANDOFF APPROVAL REQUIRED
                                            </div>
                                            <div className="text-on-surface text-[12px] font-mono leading-relaxed">
                                                The swarm is requesting permission to route the task to: <br />
                                                <span className="text-secondary font-bold text-[13px] bg-secondary/10 px-2 rounded border border-secondary/20 mt-1 inline-block">{log.next_node}</span>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="bg-surface-container/30 border border-ghost-border/10 rounded-md p-3 shadow-sm hover:border-ghost-border/30 transition-colors">
                                            <div className="flex items-center gap-2 mb-2 border-b border-ghost-border/10 pb-2">
                                                <div className="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(137,206,255,0.8)]"></div>
                                                <div className="text-primary font-bold tracking-wider uppercase text-[10px]">Node Exec: {log.node}</div>
                                            </div>

                                            {log.logs?.map((l: any, j: number) => (
                                                <div key={j} className="text-on-surface-variant text-[12px] font-mono whitespace-pre-wrap mb-1 pl-2 border-l border-ghost-border/10">
                                                    <span className="text-outline/50 select-none mr-2">{'>'}</span>{l.details}
                                                </div>
                                            ))}

                                            {log.next_agent && (
                                                <div className="flex items-center gap-2 mt-3 pt-2 text-[10px]">
                                                    <span className="uppercase text-outline font-bold tracking-widest">Routing</span>
                                                    <span className="material-symbols-outlined text-outline text-[14px]">arrow_right_alt</span>
                                                    <span className="text-primary bg-primary/10 px-2 py-0.5 rounded font-mono border border-primary/20 font-bold">{log.next_agent}</span>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                ) : activeSubTab === 'graph' ? (
                    <div className="absolute inset-x-0 bottom-6 top-0">
                        <GraphCanvas />
                    </div>
                ) : (
                    <div className="absolute inset-0 overflow-y-auto p-4 bg-surface-container-lowest">
                        <div className="text-[10px] uppercase font-bold tracking-widest text-outline mb-4 px-2 flex items-center justify-between">
                            <span>Modified Artifacts</span>
                            <span>{fileChanges.length} Files</span>
                        </div>
                        {fileChanges.length === 0 && (
                            <div className="h-64 flex flex-col items-center justify-center text-outline/40">
                                <span className="material-symbols-outlined text-[3rem] mb-2">history_edits</span>
                                <p className="text-xs font-mono">No file changes detected yet.</p>
                            </div>
                        )}
                        <div className="grid gap-2">
                            {fileChanges.map((path, i) => (
                                <button
                                    key={i}
                                    onClick={() => fetchFileContent(path)}
                                    className="group flex items-center gap-3 p-3 bg-surface-container-highest/30 border border-ghost-border/10 rounded-lg hover:border-primary/50 hover:bg-primary/5 transition-all text-left"
                                >
                                    <span className="material-symbols-outlined text-primary/70 group-hover:text-primary text-[1.25rem]">description</span>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-[13px] font-mono text-on-surface truncate">{path.split('/').pop()}</div>
                                        <div className="text-[10px] text-outline truncate font-mono opacity-60 italic">{path}</div>
                                    </div>
                                    <span className="material-symbols-outlined text-outline/30 group-hover:text-primary transition-colors text-[1rem]">arrow_forward</span>
                                </button>
                            ))}
                        </div>

                        {/* Diff Legend Placeholder */}
                        {fileChanges.length > 0 && (
                            <div className="mt-8 pt-8 border-t border-ghost-border/10">
                                <div className="text-[10px] font-bold text-outline uppercase tracking-widest mb-4">Legend</div>
                                <div className="space-y-2">
                                    <div className="flex items-center gap-3 text-[11px] text-on-surface-variant font-mono">
                                        <span className="w-3 h-3 bg-primary/20 border border-primary/40 rounded-sm"></span>
                                        Modified by Agent
                                    </div>
                                    <div className="text-[10px] text-outline italic leading-relaxed py-2 bg-surface-container-low px-3 rounded border border-ghost-border/10">
                                        Click on a file to view current content. Multi-version diff view coming soon.
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Editor Footer */}
            <div className="h-6 bg-surface-container-low flex items-center px-4 justify-between shrink-0 border-t border-ghost-border/10">
                <div className="flex items-center gap-4 text-[10px] text-outline uppercase font-mono tracking-widest">
                    <div className="flex items-center gap-1"><span className="material-symbols-outlined text-[12px]">code_blocks</span> UTF-8</div>
                    <div className="flex items-center gap-1"><span className="material-symbols-outlined text-[12px]">terminal</span> Shell Output</div>
                </div>
                <div className="text-[10px] text-outline font-mono">Count: {logs.length}</div>
            </div>
        </div>
    );
}
