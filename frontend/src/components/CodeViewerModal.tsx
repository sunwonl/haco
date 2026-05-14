import { motion, AnimatePresence } from 'framer-motion'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useHarnessStore } from '../store/useHarnessStore'
import { useEffect } from 'react'

export default function CodeViewerModal() {
    const isOpen = useHarnessStore(s => s.isCodeViewerOpen)
    const setIsOpen = useHarnessStore(s => s.setIsCodeViewerOpen)
    const content = useHarnessStore(s => s.fileContent)
    const path = useHarnessStore(s => s.currentFilePath)

    // Close on ESC
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') setIsOpen(false)
        }
        window.addEventListener('keydown', handleEsc)
        return () => window.removeEventListener('keydown', handleEsc)
    }, [setIsOpen])

    const getLanguage = (filename: string) => {
        const ext = filename.split('.').pop()?.toLowerCase()
        if (ext === 'py') return 'python'
        if (ext === 'js' || ext === 'jsx') return 'javascript'
        if (ext === 'ts' || ext === 'tsx') return 'typescript'
        if (ext === 'json') return 'json'
        if (ext === 'md') return 'markdown'
        if (ext === 'css') return 'css'
        if (ext === 'html') return 'html'
        return 'text'
    }

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-12">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsOpen(false)}
                        className="absolute inset-0 bg-background/60 backdrop-blur-md"
                    />

                    {/* Modal Content */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                        className="relative w-full max-w-6xl h-full max-h-[85vh] bg-surface-container-lowest rounded-2xl shadow-2xl border border-ghost-border/20 flex flex-col overflow-hidden"
                    >
                        {/* Header */}
                        <div className="px-6 py-4 border-b border-ghost-border/10 flex items-center justify-between bg-surface-container-low/50">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-primary/10 rounded-lg">
                                    <span className="material-symbols-outlined text-primary text-[20px]">
                                        {path.endsWith('.py') ? 'python' : 'description'}
                                    </span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-[14px] font-bold text-on-surface tracking-tight">{path.split('/').pop()}</span>
                                    <span className="text-[10px] text-outline font-mono opacity-60">{path}</span>
                                </div>
                            </div>
                            
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => {
                                        if (content) {
                                            navigator.clipboard.writeText(content)
                                            // TODO: Add toast notification
                                        }
                                    }}
                                    className="p-2 hover:bg-surface-container-high rounded-full transition-colors text-outline hover:text-on-surface"
                                    title="Copy Code"
                                >
                                    <span className="material-symbols-outlined text-[18px]">content_copy</span>
                                </button>
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="p-2 hover:bg-error/10 hover:text-error rounded-full transition-colors text-outline"
                                >
                                    <span className="material-symbols-outlined text-[20px]">close</span>
                                </button>
                            </div>
                        </div>

                        {/* Code Body */}
                        <div className="flex-1 overflow-auto bg-[#1a1b26] p-4 font-mono text-[13px] leading-relaxed relative">
                            {content ? (
                                <SyntaxHighlighter
                                    language={getLanguage(path)}
                                    style={atomDark}
                                    customStyle={{
                                        margin: 0,
                                        padding: '1rem',
                                        background: 'transparent',
                                        fontSize: 'inherit',
                                        lineHeight: 'inherit'
                                    }}
                                    showLineNumbers={true}
                                    lineNumberStyle={{ minWidth: '3em', paddingRight: '1em', color: '#565f89', textAlign: 'right' }}
                                >
                                    {content}
                                </SyntaxHighlighter>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-outline/30">
                                    <span className="material-symbols-outlined text-[3rem] mb-2 animate-pulse">sync</span>
                                    <span className="text-xs uppercase tracking-widest font-bold">Loading Content...</span>
                                </div>
                            )}
                        </div>

                        {/* Footer Status */}
                        <div className="px-6 py-2 border-t border-ghost-border/10 bg-surface-container-lowest flex items-center justify-between text-[10px] text-outline font-mono uppercase tracking-widest">
                            <div className="flex items-center gap-4">
                                <span>Language: <span className="text-primary font-bold">{getLanguage(path)}</span></span>
                                <span>Lines: <span className="text-on-surface-variant font-bold">{content?.split('\n').length || 0}</span></span>
                            </div>
                            <div className="opacity-40">ESC to close</div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
