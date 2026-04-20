import { useEffect, useRef } from 'react';

type Message = { id: string, role: 'user' | 'assistant', text: string, intent?: string };

export default function ChatWorkspace({
    messages, isRunning, prompt, setPrompt, handleRun, isInterrupted, resumeRun, activeNode
}: {
    messages: Message[], isRunning: boolean, prompt: string, setPrompt: (v: string) => void,
    handleRun: () => void, isInterrupted: boolean, resumeRun: () => void, activeNode: string | null
}) {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isRunning]);

    const activeText = activeNode ? `${activeNode} is executing...` : 'System Idle';

    return (
        <div className="flex-[0.8] bg-surface-container-low border-r border-ghost-border/15 flex flex-col relative shrink-[0.5] shadow-inner">
            {/* Active Agent Status Bar */}
            <div className="absolute top-0 left-0 right-0 h-12 bg-surface-container flex items-center px-6 justify-between z-10 border-b border-ghost-border/15 shadow-[0_4px_12px_rgba(0,0,0,0.1)]">
                <div className="flex items-center gap-4">
                    <div className="flex -space-x-2">
                        <div className="w-8 h-8 rounded-full bg-surface-container-lowest flex items-center justify-center ring-2 ring-surface-container relative select-none">
                            <span className="material-symbols-outlined text-[1rem]">architecture</span>
                        </div>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ring-2 ring-surface-container z-10 relative shadow-md select-none ${isRunning ? 'bg-primary border border-primary/30' : 'bg-surface-container-highest'}`}>
                            <span className={`material-symbols-outlined text-[1rem] ${isRunning ? 'text-on-primary' : 'text-on-surface'}`} data-weight="fill">code</span>
                        </div>
                        <div className="w-8 h-8 rounded-full bg-surface-container-lowest flex items-center justify-center ring-2 ring-surface-container relative select-none">
                            <span className="material-symbols-outlined text-[1rem]">policy</span>
                        </div>
                    </div>
                    <div className="flex flex-col mt-0.5">
                        <span className={`text-[10px] font-bold uppercase tracking-widest ${isRunning ? 'text-primary' : 'text-outline'}`}>
                            {activeNode || 'Swarm'} {isRunning ? '(Active)' : '(Standby)'}
                        </span>
                        <span className="text-[11px] text-on-surface-variant max-w-[200px] truncate">{activeText}</span>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-primary animate-pulse shadow-[0_0_8px_rgba(137,206,255,0.8)]' : 'bg-outline'}`}></span>
                    <span className="text-[10px] text-on-surface-variant font-mono uppercase tracking-widest">
                        {isRunning ? 'THINKING' : 'IDLE'}
                    </span>
                </div>
            </div>

            {/* Chat History */}
            <div className="flex-1 overflow-y-auto pt-16 pb-6 px-8 flex flex-col gap-8" ref={scrollRef}>
                {messages.length === 0 && (
                    <div className="m-auto flex flex-col items-center justify-center text-center opacity-70">
                        <span className="material-symbols-outlined text-[3rem] mb-4 text-primary opacity-50">forum</span>
                        <h2 className="text-xl font-bold mb-2 text-on-surface">SYNTHETIC SWARM</h2>
                        <p className="text-on-surface-variant text-[0.875rem] font-mono leading-relaxed max-w-sm">
                            Multi-agent routing system online.<br />Awaiting user prompt...
                        </p>
                    </div>
                )}

                {messages.map(msg => (
                    <div key={msg.id} className="flex gap-4 group">
                        <div className={`w-8 h-8 rounded shrink-0 flex items-center justify-center shadow-sm select-none ${msg.role === 'user' ? 'bg-surface-container-highest border border-ghost-border/20' : 'bg-primary/20 border border-primary/30 text-primary drop-shadow-[0_0_8px_rgba(137,206,255,0.2)]'}`}>
                            <span className="material-symbols-outlined text-[1.125rem]" data-weight={msg.role !== 'user' ? 'fill' : 'normal'}>
                                {msg.role === 'user' ? 'person' : 'smart_toy'}
                            </span>
                        </div>
                        <div className="flex flex-col gap-2 w-full max-w-[90%]">
                            <div className={`text-[11px] font-bold uppercase tracking-wider ${msg.role === 'user' ? 'text-outline' : 'text-primary'}`}>
                                {msg.role === 'user' ? 'User' : 'Agent'}
                            </div>
                            {msg.role === 'user' ? (
                                <p className="text-sm leading-relaxed text-on-surface font-medium whitespace-pre-wrap">{msg.text}</p>
                            ) : (
                                <div className="bg-surface-container-highest p-4 rounded-xl border-l-[3px] border-primary shadow-[0_8px_24px_rgba(0,0,0,0.3)]">
                                    <p className="text-[0.9375rem] leading-relaxed text-on-surface mb-3 whitespace-pre-wrap">{msg.text}</p>
                                    {msg.intent && (
                                        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-ghost-border/20">
                                            <span className="text-[10px] text-primary bg-primary/10 px-2 py-0.5 rounded uppercase font-mono tracking-widest">{msg.intent}</span>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Input Area */}
            <div className="p-4 bg-surface-container shadow-[0_-8px_32px_rgba(0,0,0,0.2)] z-20">
                <div className="relative group">
                    <textarea
                        className="w-full bg-surface-container-highest border border-outline-variant/20 rounded-xl p-4 pr-14 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:border-primary/50 transition-all resize-none min-h-[90px] shadow-inner font-mono"
                        placeholder={isInterrupted ? "Pipeline paused. Type response or 'Approve' and send..." : "Ask the swarm to code, refactor or debug..."}
                        value={prompt}
                        onChange={e => setPrompt(e.target.value)}
                        onKeyDown={e => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleRun();
                            }
                        }}
                        disabled={isRunning && !isInterrupted}
                    />

                    {isInterrupted ? (
                        <button
                            onClick={resumeRun}
                            disabled={isRunning}
                            className="absolute bottom-4 right-16 p-2 bg-secondary text-on-secondary rounded-lg shadow-lg hover:scale-105 transition-transform flex items-center gap-1 font-bold text-xs"
                        >
                            <span className="material-symbols-outlined text-[1rem]">check_circle</span>
                            APPROVE
                        </button>
                    ) : null}

                    <button
                        onClick={handleRun}
                        disabled={!prompt.trim() || (isRunning && !isInterrupted)}
                        className={`absolute bottom-4 right-4 p-2 rounded-lg shadow-lg transition-transform ${(!prompt.trim() || (isRunning && !isInterrupted)) ? 'bg-surface-container-high text-outline cursor-not-allowed' : 'bg-primary text-on-primary hover:scale-105 shadow-primary/20'}`}
                    >
                        <span className="material-symbols-outlined text-[1.25rem]">send</span>
                    </button>
                </div>
                <div className="mt-2 flex items-center gap-4 px-2">
                    <button className="text-[10px] text-outline hover:text-primary transition-colors flex items-center gap-1 font-mono uppercase">
                        <span className="material-symbols-outlined text-[0.875rem]">attach_file</span> Attach context
                    </button>
                    <button className="text-[10px] text-outline hover:text-primary transition-colors flex items-center gap-1 font-mono uppercase">
                        <span className="material-symbols-outlined text-[0.875rem]">history</span> Session history
                    </button>
                </div>
            </div>
        </div>
    )
}
