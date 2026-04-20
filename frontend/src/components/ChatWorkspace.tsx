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
        <div className="flex-1 w-full h-full bg-surface-container-low border-r border-ghost-border/15 flex flex-col relative shadow-inner overflow-hidden">
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
            <div className="flex-1 overflow-y-auto pt-16 pb-32 px-8 flex flex-col gap-8 scroll-smooth" ref={scrollRef}>
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
                    <div key={msg.id} className="flex gap-4 group animate-in fade-in slide-in-from-bottom-2 duration-500">
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
                                <div className="bg-surface-container/40 p-4 rounded-xl border-l-[3px] border-primary shadow-[0_8px_24px_rgba(0,0,0,0.1)] backdrop-blur-sm">
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

            {/* Input Area - Positioned at true bottom */}
            <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-surface-container-low via-surface-container-low/95 to-transparent z-20">
                <div className="max-w-4xl mx-auto space-y-3">
                    {/* HITL Banner */}
                    {isInterrupted && (
                        <div className="bg-secondary/15 border border-secondary/30 rounded-xl p-3 flex items-center gap-4 animate-in slide-in-from-bottom-4 fade-in duration-500 shadow-lg backdrop-blur-md">
                            <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center text-secondary shrink-0 animate-pulse">
                                <span className="material-symbols-outlined text-[1.5rem]" data-weight="fill">front_hand</span>
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="text-[10px] font-bold uppercase tracking-widest text-secondary mb-0.5">Approval Required</div>
                                <div className="text-[13px] text-on-surface font-medium truncate">
                                    Agent is waiting to hand off to <span className="text-secondary font-bold font-mono px-1.5 py-0.5 bg-secondary/10 rounded border border-secondary/20 ml-1">{activeNode || 'Next Node'}</span>
                                </div>
                            </div>
                            <button
                                onClick={() => resumeRun()}
                                className="px-4 py-2 bg-secondary text-on-secondary rounded-xl font-bold text-[11px] uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-lg shadow-secondary/20 flex items-center gap-2 shrink-0 group"
                            >
                                <span className="material-symbols-outlined text-[1.125rem] group-hover:rotate-12 transition-transform">check_circle</span>
                                Approve
                            </button>
                        </div>
                    )}

                    <div className="relative group">
                        <textarea
                            className={`w-full bg-surface-container-highest/80 backdrop-blur-md border rounded-2xl p-5 pr-16 text-sm text-on-surface placeholder:text-outline/50 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all resize-none min-h-[80px] shadow-2xl font-mono
                                ${isInterrupted ? 'border-secondary/40 shadow-secondary/5 ring-secondary/10' : 'border-ghost-border/30 shadow-black/20'}`}
                            placeholder={isInterrupted ? "Type custom instructions to redirect or 'Approve' to proceed..." : "Ask the swarm to code, refactor or debug..."}
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

                        <div className="absolute right-4 bottom-4 flex items-center gap-2">
                            <button
                                onClick={handleRun}
                                disabled={!prompt.trim() || (isRunning && !isInterrupted)}
                                className={`p-2 rounded-xl shadow-lg transition-all ${(!prompt.trim() || (isRunning && !isInterrupted)) ? 'bg-surface-container-high text-outline cursor-not-allowed opacity-50' : isInterrupted ? 'bg-secondary text-on-secondary hover:scale-105 active:scale-95 shadow-secondary/30' : 'bg-primary text-on-primary hover:scale-105 active:scale-95 shadow-primary/30'}`}
                            >
                                <span className="material-symbols-outlined text-[1.25rem]">{isInterrupted ? 'edit_note' : 'send'}</span>
                            </button>
                        </div>
                    </div>
                </div>
                <div className="mt-3 flex items-center justify-center gap-6 px-2 opacity-50 hover:opacity-100 transition-opacity">
                    <button className="text-[9px] text-outline hover:text-primary transition-colors flex items-center gap-1 font-mono uppercase tracking-widest">
                        <span className="material-symbols-outlined text-[0.875rem]">attach_file</span> Context
                    </button>
                    <button className="text-[9px] text-outline hover:text-primary transition-colors flex items-center gap-1 font-mono uppercase tracking-widest">
                        <span className="material-symbols-outlined text-[0.875rem]">history</span> History
                    </button>
                    <button className="text-[9px] text-outline hover:text-primary transition-colors flex items-center gap-1 font-mono uppercase tracking-widest">
                        <span className="material-symbols-outlined text-[0.875rem]">settings_input_component</span> Agents
                    </button>
                </div>
            </div>
        </div>
    )
}
