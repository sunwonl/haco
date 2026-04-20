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
        <div className="w-64 bg-surface-container-low flex flex-col border-r border-ghost-border/15 shrink-0">
            {/* Header */}
            <div className="px-4 py-3 flex items-center justify-between border-b border-ghost-border/15 shadow-sm">
                <span className="text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                    {currentPath === '.' ? 'Project_Root' : currentPath}
                </span>
                <div className="flex gap-1">
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
            <div className="px-4 py-3 border-b border-ghost-border/10">
                <div className="text-[10px] text-outline uppercase tracking-tighter mb-1">Session</div>
                <div className="flex items-center gap-2 text-on-surface-variant text-[11px] font-mono opacity-80">
                    <span className="material-symbols-outlined text-sm text-secondary">commit</span>
                    <span>{threadId ? `Thread: ${threadId.substring(0, 8)}` : 'No session'}</span>
                </div>
            </div>

            {/* File List */}
            <div className="flex-1 overflow-y-auto py-2">
                {files.length === 0 ? (
                    <div className="px-4 py-3 text-outline text-[11px] font-mono">Loading...</div>
                ) : (
                    files.map(entry => (
                        <button
                            key={entry.path}
                            onClick={() => handleClick(entry)}
                            className={`w-full flex items-center gap-2 px-3 py-1.5 text-[12px] hover:bg-surface-container transition-colors text-left
                                ${expandedFile === entry.path ? 'bg-surface-container-highest text-primary border-l-2 border-primary' : 'text-on-surface-variant border-l-2 border-transparent'}`}
                        >
                            <span className="material-symbols-outlined text-[1rem] shrink-0">
                                {entry.type === 'directory' ? 'folder' : 'description'}
                            </span>
                            <span className="truncate">{entry.name}</span>
                            {entry.type === 'file' && entry.size != null && (
                                <span className="ml-auto text-[10px] text-outline shrink-0">
                                    {entry.size > 1024 ? `${(entry.size / 1024).toFixed(1)}k` : `${entry.size}b`}
                                </span>
                            )}
                        </button>
                    ))
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
