import { useState } from 'react'
import { useHarnessStore } from '../store/useHarnessStore'

interface FileExplorerProps {
    onFetchFiles: (path: string) => void
    onFetchContent: (path: string) => void
}

export default function FileExplorer({ onFetchFiles, onFetchContent }: FileExplorerProps) {
    const files = useHarnessStore(s => s.files)
    const currentPath = useHarnessStore(s => s.currentFilePath)
    const fileContent = useHarnessStore(s => s.fileContent)
    const threadId = useHarnessStore(s => s.threadId)
    const fileChanges = useHarnessStore(s => s.fileChanges)

    const [expandedFile, setExpandedFile] = useState<string | null>(null)

    const handleClick = (entry: { type: string; path: string; name: string }) => {
        if (entry.type === 'directory') {
            onFetchFiles(entry.path)
        } else {
            setExpandedFile(entry.path)
            onFetchContent(entry.path)
        }
    }

    const handleBack = () => {
        const parent = currentPath.includes('/') ? currentPath.split('/').slice(0, -1).join('/') || '.' : '.'
        onFetchFiles(parent)
        setExpandedFile(null)
    }

    return (
        <div className="w-64 bg-surface-container-low flex flex-col border-r border-ghost-border/15 shrink-0 h-full overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 flex items-center justify-between border-b border-ghost-border/15 shadow-sm">
                <span className="text-[11px] font-bold uppercase tracking-widest text-on-surface-variant truncate pr-2">
                    {currentPath === '.' ? 'Project_Root' : currentPath}
                </span>
                <div className="flex gap-1 shrink-0">
                    {currentPath !== '.' && (
                        <button onClick={handleBack} title="Go up" className="text-outline hover:text-on-surface transition-colors">
                            <span className="material-symbols-outlined text-[1rem]">arrow_upward</span>
                        </button>
                    )}
                    <button onClick={() => onFetchFiles(currentPath)} title="Refresh" className="text-outline hover:text-on-surface transition-colors">
                        <span className="material-symbols-outlined text-[1rem]">refresh</span>
                    </button>
                </div>
            </div>

            {/* Session info */}
            <div className="px-4 py-2 border-b border-ghost-border/10 bg-surface-container/50">
                <div className="text-[9px] text-outline uppercase tracking-tighter mb-1 opacity-60">Active Session</div>
                <div className="flex items-center gap-2 text-on-surface-variant text-[11px] font-mono">
                    <div className="w-1.5 h-1.5 border border-secondary rounded-full animate-pulse bg-secondary"></div>
                    <span className="truncate">{threadId ? threadId.substring(0, 12) : 'STANDBY'}</span>
                </div>
            </div>

            {/* File List */}
            <div className="flex-1 overflow-y-auto py-1 no-scrollbar">
                {files.length === 0 ? (
                    <div className="px-4 py-8 flex flex-col items-center justify-center text-outline/40">
                        <span className="material-symbols-outlined text-[1.5rem] mb-1 animate-spin">sync</span>
                        <div className="text-[10px] font-mono">Exploring...</div>
                    </div>
                ) : (
                    files.map(entry => {
                        const isModified = fileChanges.includes(entry.path);
                        const isSelected = expandedFile === entry.path;

                        return (
                            <button
                                key={entry.path}
                                onClick={() => handleClick(entry)}
                                className={`w-full flex items-center gap-2 px-3 py-1.5 text-[12px] transition-all text-left relative group
                                    ${isSelected
                                        ? 'bg-primary/10 text-primary border-l-[3px] border-primary font-bold'
                                        : isModified
                                            ? 'bg-secondary/5 text-secondary border-l-[3px] border-secondary/40 hover:bg-secondary/10'
                                            : 'text-on-surface-variant border-l-[3px] border-transparent hover:bg-surface-container-highest/50'
                                    }`}
                            >
                                <span className={`material-symbols-outlined text-[1rem] shrink-0 ${isModified && !isSelected ? 'text-secondary' : isSelected ? 'text-primary' : 'text-outline/70'}`}>
                                    {entry.type === 'directory' ? 'folder' : 'description'}
                                </span>
                                <span className="truncate flex-1">{entry.name}</span>

                                {isModified && (
                                    <span className="text-[8px] bg-secondary/20 text-secondary px-1 rounded font-bold uppercase tracking-tighter shrink-0 animate-in fade-in zoom-in">MOD</span>
                                )}

                                {entry.type === 'file' && !isModified && entry.size != null && (
                                    <span className="text-[9px] text-outline/40 font-mono hidden group-hover:block transition-all">
                                        {entry.size > 1024 ? `${(entry.size / 1024).toFixed(1)}K` : `${entry.size}B`}
                                    </span>
                                )}
                            </button>
                        );
                    })
                )}
            </div>

            {/* Inline file content preview (collapsible) */}
            {fileContent && expandedFile && (
                <div className="border-t border-ghost-border/20 bg-surface-container-lowest max-h-40 overflow-y-auto">
                    <div className="px-3 py-1.5 flex items-center justify-between border-b border-ghost-border/10">
                        <span className="text-[10px] text-outline font-mono truncate">{expandedFile}</span>
                        <button onClick={() => setExpandedFile(null)} className="text-outline hover:text-on-surface">
                            <span className="material-symbols-outlined text-[12px]">close</span>
                        </button>
                    </div>
                    <pre className="text-[10px] px-3 py-2 text-on-surface-variant font-mono leading-4 whitespace-pre-wrap break-all">{fileContent.substring(0, 500)}</pre>
                </div>
            )}
        </div>
    )
}
