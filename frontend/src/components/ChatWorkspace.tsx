import { useEffect, useRef } from 'react';
import { useHarnessStore } from '../store/useHarnessStore';

type Message = { id: string, role: 'user' | 'assistant', text: string, intent?: string, category?: string, agent?: string };

const AGENT_CONFIG: Record<string, { label: string, color: string, bg: string, border: string, icon: string }> = {
    'PO': { label: 'Product Owner', color: 'text-blue-500', bg: 'bg-blue-500/20', border: 'border-blue-500', icon: 'description' },
    'SA': { label: 'Software Architect', color: 'text-purple-500', bg: 'bg-purple-500/20', border: 'border-purple-500', icon: 'architecture' },
    'CD': { label: 'Core Developer', color: 'text-emerald-500', bg: 'bg-emerald-500/20', border: 'border-emerald-500', icon: 'code' },
    'DR': { label: 'Design Reviewer', color: 'text-amber-500', bg: 'bg-amber-500/20', border: 'border-amber-500', icon: 'palette' },
    'QA': { label: 'Quality Assurance', color: 'text-rose-500', bg: 'bg-rose-500/20', border: 'border-rose-500', icon: 'fact_check' },
    'System': { label: 'System', color: 'text-slate-400', bg: 'bg-slate-400/10', border: 'border-slate-400/30', icon: 'settings' },
    'Interrupt': { label: 'Pipeline Interrupted', color: 'text-secondary', bg: 'bg-secondary/10', border: 'border-secondary/40', icon: 'front_hand' }
};

const getAgentStyle = (msg: Message) => {
    if (msg.role === 'user') return null;
    if (msg.category === 'Interrupt') return AGENT_CONFIG['Interrupt'];
    if (msg.category === 'System') return AGENT_CONFIG['System'];
    return AGENT_CONFIG[msg.agent || ''] || { label: msg.agent || 'Agent', color: 'text-primary', bg: 'bg-primary/20', border: 'border-primary', icon: 'smart_toy' };
};

const JOURNEY_AGENTS = ['PO', 'SA', 'CD', 'QA'];

export default function ChatWorkspace({
    messages, isRunning, prompt, setPrompt, handleRun, isInterrupted, resumeRun, activeNode
}: {
    messages: Message[], isRunning: boolean, prompt: string, setPrompt: (v: string) => void,
    handleRun: () => void, isInterrupted: boolean, resumeRun: (feedback?: string) => void, activeNode: string | null
}) {
    const scrollRef = useRef<HTMLDivElement>(null);
    const interruptDetails = useHarnessStore(s => s.interruptDetails);
    const streamingMessageId = useHarnessStore(s => s.streamingMessageId);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isRunning]);

    const activeText = activeNode ? `${AGENT_CONFIG[activeNode]?.label || activeNode} is executing...` : 'System Idle';

    return (
        <div className="flex-1 w-full h-full bg-surface-container-low border-r border-ghost-border/15 flex flex-col relative shadow-inner overflow-hidden">
            {/* 1. Agent Journey Stepper (Top Bar) */}
            <div className="h-14 bg-surface-container flex items-center px-8 justify-between z-10 border-b border-ghost-border/15 shadow-[0_4px_12px_rgba(0,0,0,0.05)] shrink-0">
                <div className="flex items-center gap-10">
                    {JOURNEY_AGENTS.map((role, idx) => {
                        const config = AGENT_CONFIG[role];
                        const isActive = activeNode === role && isRunning;
                        const isPast = !isActive && messages.some(m => m.agent === role);
                        
                        return (
                            <div key={role} className="flex items-center gap-3 group relative">
                                <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all duration-500 shadow-sm
                                    ${isActive ? `${config.bg} ${config.border} scale-110 ring-4 ring-primary/10` : 
                                      isPast ? 'bg-emerald-500/10 border-emerald-500/40 opacity-70' : 'bg-surface-container-highest border-ghost-border/20 opacity-30'}`}>
                                    <span className={`material-symbols-outlined text-[1rem] ${isActive ? config.color : isPast ? 'text-emerald-500' : 'text-outline'}`} data-weight={isActive ? 'fill' : 'normal'}>
                                        {isActive && isRunning ? config.icon : (isPast ? 'check_circle' : config.icon)}
                                    </span>
                                </div>
                                <div className="flex flex-col">
                                    <span className={`text-[9px] font-black uppercase tracking-tighter transition-colors ${isActive ? config.color : 'text-outline'}`}>
                                        {role}
                                    </span>
                                    {isActive && (
                                        <span className="absolute -bottom-4 left-0 text-[8px] font-bold text-primary animate-pulse whitespace-nowrap">
                                            Executing...
                                        </span>
                                    )}
                                </div>
                                {idx < JOURNEY_AGENTS.length - 1 && (
                                    <div className="absolute -right-7 top-1/2 -translate-y-1/2 w-4 h-[1px] bg-ghost-border/20" />
                                )}
                            </div>
                        );
                    })}
                </div>

                <div className="flex items-center gap-3 bg-surface-container-lowest px-3 py-1.5 rounded-full border border-ghost-border/10">
                    <span className={`w-1.5 h-1.5 rounded-full ${isRunning ? 'bg-primary animate-pulse shadow-[0_0_8px_rgba(137,206,255,0.8)]' : 'bg-outline/30'}`}></span>
                    <span className="text-[9px] text-on-surface-variant font-mono uppercase tracking-[0.2em] font-black">
                        {isRunning ? 'Swarm_Online' : 'Idle'}
                    </span>
                </div>
            </div>

            {/* 2. Global Activity Progress Bar (Subtle) */}
            <div className={`h-0.5 w-full overflow-hidden transition-opacity duration-500 ${isRunning && !isInterrupted ? 'opacity-100' : 'opacity-0'}`}>
                <div className="h-full bg-primary animate-progress-flow"></div>
            </div>

            {/* Chat History */}
            <div className="flex-1 overflow-y-auto pt-8 pb-8 px-8 flex flex-col gap-8 scroll-smooth" ref={scrollRef}>
                {messages.length === 0 && (
                    <div className="m-auto flex flex-col items-center justify-center text-center opacity-70">
                        <span className="material-symbols-outlined text-[3rem] mb-4 text-primary opacity-50">forum</span>
                        <h2 className="text-xl font-bold mb-2 text-on-surface">SYNTHETIC SWARM</h2>
                        <p className="text-on-surface-variant text-[0.875rem] font-mono leading-relaxed max-w-sm">
                            Multi-agent routing system online.<br />Awaiting user prompt...
                        </p>
                    </div>
                )}

                {messages.map(msg => {
                    const style = getAgentStyle(msg);
                    return (
                        <div key={msg.id} className="flex gap-4 group animate-in fade-in slide-in-from-bottom-2 duration-500">
                            <div className={`w-8 h-8 rounded shrink-0 flex items-center justify-center shadow-sm select-none 
                                ${msg.role === 'user' ? 'bg-surface-container-highest border border-ghost-border/20' : (style?.bg + ' border ' + style?.border + ' ' + style?.color)}`}>
                                <span className={`material-symbols-outlined text-[1.125rem]`} data-weight={msg.role !== 'user' ? 'fill' : 'normal'}>
                                    {msg.role === 'user' ? 'person' : (style?.icon || 'smart_toy')}
                                </span>
                            </div>
                            <div className="flex flex-col gap-2 w-full max-w-[90%]">
                                <div className={`text-[10px] font-black uppercase tracking-widest ${msg.role === 'user' ? 'text-outline' : (style?.color || 'text-primary')}`}>
                                    {msg.role === 'user' ? 'USER' : (style?.label || 'AGENT')}
                                </div>
                                {msg.role === 'user' ? (
                                    <p className="text-sm leading-relaxed text-on-surface font-medium whitespace-pre-wrap">{msg.text}</p>
                                ) : (
                                    <div className={`p-4 rounded-xl border-l-[3px] shadow-[0_8px_24px_rgba(0,0,0,0.06)] backdrop-blur-sm transition-all duration-300
                                        ${msg.category === 'Interrupt' ? 'bg-secondary/10 border-secondary' :
                                            msg.category === 'Thought' ? 'bg-primary/5 border-primary/20 opacity-80' :
                                                msg.category === 'System' ? 'bg-slate-400/5 border-slate-400 font-mono text-[11px]' :
                                                    `bg-surface-container/40 ${style?.border || 'border-primary'}`}`}>

                                        {msg.category === 'Thought' && (
                                            <div className="flex items-center gap-1.5 mb-2 opacity-60">
                                                <span className="material-symbols-outlined text-sm animate-pulse">psychology</span>
                                                <span className="text-[10px] font-black uppercase tracking-tighter text-primary">Thinking Process</span>
                                            </div>
                                        )}

                                        <p className={`text-[0.9375rem] leading-relaxed mb-3 whitespace-pre-wrap ${msg.category === 'Thought' ? 'text-on-surface-variant italic font-inter' : 'text-on-surface'}`}>
                                            {msg.text}
                                            {isRunning && msg.id === streamingMessageId && (
                                                <span className="inline-block w-1.5 h-4 ml-1 bg-primary animate-pulse align-middle rounded-full"></span>
                                            )}
                                        </p>

                                        {msg.intent && msg.category !== 'Thought' && (
                                            <div className="flex items-center gap-2 mt-3 pt-3 border-t border-ghost-border/10">
                                                <span className={`text-[9px] px-2 py-0.5 rounded uppercase font-bold tracking-widest ${style?.bg} ${style?.color}`}>{msg.intent}</span>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Input Area */}
            <div className="p-6 bg-surface-container-low border-t border-ghost-border/15 shrink-0 z-20">
                <div className="max-w-4xl mx-auto space-y-4">
                    {/* HITL Panel */}
                    {isInterrupted && interruptDetails && (
                        <div className="bg-surface-container-high border border-secondary/30 rounded-2xl p-5 animate-in slide-in-from-bottom-4 duration-500 shadow-xl overflow-hidden relative">
                            {/* ... (HITL details) ... */}
                            <div className="flex flex-col gap-4 relative">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div className="px-2 py-1 bg-primary/10 text-primary text-[10px] font-black rounded uppercase tracking-tighter border border-primary/20">
                                            {interruptDetails.sender || 'Sender'}
                                        </div>
                                        <span className="material-symbols-outlined text-outline text-sm">arrow_forward</span>
                                        <div className="px-2 py-1 bg-secondary/10 text-secondary text-[10px] font-black rounded uppercase tracking-tighter border border-secondary/20">
                                            {interruptDetails.receiver || 'Receiver'}
                                        </div>
                                    </div>
                                    <span className="text-[10px] font-black text-secondary uppercase tracking-[0.2em]">Approval_Pending</span>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[9px] font-bold text-outline uppercase tracking-widest">Hand-off Request Context</label>
                                    <div className="bg-surface-container-lowest/50 p-4 rounded-xl border border-ghost-border/10">
                                        <p className="text-xs text-on-surface leading-loose font-inter italic opacity-90">
                                            "{interruptDetails.content || 'No detailed context provided.'}"
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 pt-2">
                                    <button onClick={() => resumeRun()} className="flex-1 py-2.5 bg-secondary text-on-secondary rounded-xl font-black text-[11px] uppercase tracking-widest hover:brightness-110 active:scale-[0.98] transition-all shadow-lg shadow-secondary/20 flex items-center justify-center gap-2">
                                        <span className="material-symbols-outlined text-[1.125rem]">check_circle</span> Approve & Proceed
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 3. Live Typing Indicator */}
                    {isRunning && !isInterrupted && (
                        <div className="flex items-center gap-3 mb-2 px-1 animate-in fade-in slide-in-from-bottom-1 duration-300">
                            <div className="flex gap-1">
                                <span className={`w-1 h-1 rounded-full animate-bounce [animation-delay:-0.3s] ${AGENT_CONFIG[activeNode || '']?.bg.replace('/20', '') || 'bg-primary'}`}></span>
                                <span className={`w-1 h-1 rounded-full animate-bounce [animation-delay:-0.15s] ${AGENT_CONFIG[activeNode || '']?.bg.replace('/20', '') || 'bg-primary'}`}></span>
                                <span className={`w-1 h-1 rounded-full animate-bounce ${AGENT_CONFIG[activeNode || '']?.bg.replace('/20', '') || 'bg-primary'}`}></span>
                            </div>
                            <span className={`text-[10px] font-black uppercase tracking-widest opacity-90 ${AGENT_CONFIG[activeNode || '']?.color || 'text-primary'}`}>
                                {activeText}
                            </span>
                        </div>
                    )}

                    <div className="relative group">
                        <textarea
                            className={`w-full backdrop-blur-md border rounded-2xl p-5 pr-16 text-sm text-on-surface placeholder:text-outline/50 focus:outline-none focus:ring-2 transition-all resize-none min-h-[80px] shadow-sm font-inter
                                ${isRunning && !isInterrupted ? 'bg-primary/5 border-primary/20 ring-primary/5' : 
                                  isInterrupted ? 'bg-surface-container-highest/50 border-secondary/40 ring-secondary/10' : 'bg-surface-container-highest/50 border-ghost-border/30 focus:ring-primary/30'}`}
                            placeholder={isRunning && !isInterrupted ? "에이전트가 작업을 수행하고 있습니다..." : isInterrupted ? "피드백을 입력하거나 '승인'을 눌러 진행하세요..." : "군단(Swarm)에게 작업을 지시하세요..."}
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

                <div className="mt-3 hidden md:flex items-center justify-center gap-6 px-2 opacity-30 hover:opacity-100 transition-opacity">
                    <div className="text-[9px] text-outline flex items-center gap-1 font-mono uppercase tracking-widest">
                        <span className="material-symbols-outlined text-[0.875rem]">keyboard_command_key</span> Enter to send
                    </div>
                    <div className="text-[9px] text-outline flex items-center gap-1 font-mono uppercase tracking-widest">
                        <span className="material-symbols-outlined text-[0.875rem]">keyboard_arrow_up</span> Shift+Enter for newline
                    </div>
                </div>
            </div>
        </div>
    );
}
