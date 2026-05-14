import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useHarnessStore } from '../store/useHarnessStore'

export default function ConsoleModal() {
    const isOpen = useHarnessStore(s => s.isConsoleOpen)
    const setIsOpen = useHarnessStore(s => s.setIsConsoleOpen)
    const journal = useHarnessStore(s => s.journal)
    
    const scrollRef = useRef<HTMLDivElement>(null)
    const [filter, setFilter] = useState<'ALL' | 'ACTION' | 'THOUGHT' | 'RESULT'>('ALL')

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [journal, isOpen])

    const filteredJournal = journal.filter(entry => {
        if (filter === 'ALL') return true
        if (filter === 'ACTION') return entry.category === 'Action'
        if (filter === 'THOUGHT') return entry.category === 'Thought'
        if (filter === 'RESULT') return entry.category === 'Result'
        return true
    })

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-12">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsOpen(false)}
                        className="absolute inset-0 bg-background/40 backdrop-blur-sm"
                    />

                    <motion.div
                        initial={{ opacity: 0, y: 100 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 100 }}
                        transition={{ type: 'spring', damping: 30, stiffness: 300 }}
                        className="relative w-full max-w-5xl h-[80vh] bg-[#0d0e12] sm:rounded-3xl shadow-2xl border border-white/5 flex flex-col overflow-hidden"
                    >
                        {/* Terminal Header */}
                        <div className="px-6 py-4 bg-[#1a1b23] border-b border-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="flex gap-1.5">
                                    <div className="w-3 h-3 rounded-full bg-[#ff5f56]" />
                                    <div className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
                                    <div className="w-3 h-3 rounded-full bg-[#27c93f]" />
                                </div>
                                <div className="h-4 w-px bg-white/10 mx-2" />
                                <h2 className="text-[11px] font-mono font-bold text-white/40 uppercase tracking-[0.2em]">HarnessCore / System Console</h2>
                            </div>
                            
                            <div className="flex items-center gap-4">
                                <div className="flex bg-white/5 p-1 rounded-xl">
                                    {(['ALL', 'THOUGHT', 'ACTION', 'RESULT'] as const).map(f => (
                                        <button
                                            key={f}
                                            onClick={() => setFilter(f)}
                                            className={`px-3 py-1 text-[9px] font-bold rounded-lg transition-all ${filter === f ? 'bg-primary text-on-primary shadow-lg shadow-primary/20' : 'text-white/40 hover:text-white/70'}`}
                                        >
                                            {f}
                                        </button>
                                    ))}
                                </div>
                                <button onClick={() => setIsOpen(false)} className="text-white/20 hover:text-white transition-colors">
                                    <span className="material-symbols-outlined text-[18px]">close</span>
                                </button>
                            </div>
                        </div>

                        {/* Terminal Body */}
                        <div 
                            ref={scrollRef}
                            className="flex-1 overflow-y-auto p-6 font-mono text-[12px] selection:bg-primary/30"
                        >
                            <div className="space-y-4">
                                {filteredJournal.length === 0 ? (
                                    <div className="h-full flex flex-col items-center justify-center opacity-20 py-20">
                                        <span className="material-symbols-outlined text-4xl mb-2">terminal</span>
                                        <p className="font-mono uppercase tracking-widest text-[10px]">Waiting for system activity...</p>
                                    </div>
                                ) : (
                                    filteredJournal.map((entry, idx) => (
                                        <div key={idx} className="flex gap-4 group">
                                            <span className="text-white/20 shrink-0 select-none w-16 text-right">[{entry.timestamp.split(' ')[1].substring(0, 8)}]</span>
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2">
                                                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-tighter ${
                                                        entry.category === 'Thought' ? 'bg-blue-500/20 text-blue-400' :
                                                        entry.category === 'Action' ? 'bg-purple-500/20 text-purple-400' :
                                                        entry.category === 'Result' ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/50'
                                                    }`}>
                                                        {entry.category}
                                                    </span>
                                                    <span className="text-white/60 font-bold">{entry.role || 'System'}</span>
                                                    {entry.target && (
                                                        <span className="text-white/20">→ {entry.target}</span>
                                                    )}
                                                </div>
                                                <pre className={`whitespace-pre-wrap break-all leading-relaxed ${
                                                    entry.category === 'Thought' ? 'text-white/40 italic' : 
                                                    entry.category === 'Result' ? 'text-green-400/80' : 'text-white/80'
                                                }`}>
                                                    {entry.content}
                                                </pre>
                                            </div>
                                        </div>
                                    ))
                                )}
                                <div className="h-4" />
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="px-6 py-3 bg-[#1a1b23] border-t border-white/5 flex items-center justify-between text-[10px] font-mono">
                            <div className="flex items-center gap-6 text-white/30">
                                <div className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                                    <span>LIVE STREAMING</span>
                                </div>
                                <span>ENTRIES: <span className="text-white/60">{filteredJournal.length}</span></span>
                            </div>
                            <div className="text-white/20 italic">Press ESC to exit console</div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
