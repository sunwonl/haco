export type TabType = 'workspace' | 'config' | 'docs';

export default function Sidebar({ activeTab, onTabChange }: { activeTab: TabType, onTabChange: (t: TabType) => void }) {
    return (
        <aside className="fixed left-0 top-0 h-full z-50 flex flex-col justify-between bg-surface-container-low w-16 py-4 border-r border-ghost-border/15">
            <div className="flex flex-col items-center gap-6">
                <div className="w-10 h-10 bg-surface-container-highest rounded-lg flex items-center justify-center mb-4 border border-outline-variant/30">
                    <span className="material-symbols-outlined text-primary text-[1.5rem]">terminal</span>
                </div>

                <nav className="flex flex-col items-center w-full gap-2">
                    <button
                        onClick={() => onTabChange('workspace')}
                        className={`w-full py-3 flex items-center justify-center transition-all duration-200 ${activeTab === 'workspace'
                            ? 'text-primary border-l-2 border-primary bg-surface-container'
                            : 'text-on-surface-variant opacity-60 hover:opacity-100 hover:bg-surface-container border-l-2 border-transparent'
                            }`}>
                        <span className="material-symbols-outlined fill-current">forum</span>
                    </button>

                    <button
                        onClick={() => onTabChange('config')}
                        className={`w-full py-3 flex items-center justify-center transition-all duration-200 ${activeTab === 'config'
                            ? 'text-primary border-l-2 border-primary bg-surface-container'
                            : 'text-on-surface-variant opacity-60 hover:opacity-100 hover:bg-surface-container border-l-2 border-transparent'
                            }`}>
                        <span className="material-symbols-outlined">settings_suggest</span>
                    </button>

                    <button
                        onClick={() => onTabChange('docs')}
                        className={`w-full py-3 flex items-center justify-center transition-all duration-200 ${activeTab === 'docs'
                            ? 'text-primary border-l-2 border-primary bg-surface-container'
                            : 'text-on-surface-variant opacity-60 hover:opacity-100 hover:bg-surface-container border-l-2 border-transparent'
                            }`}>
                        <span className="material-symbols-outlined">menu_book</span>
                    </button>
                </nav>
            </div>

            <div className="flex flex-col items-center w-full gap-2">
                <button className="w-full py-3 flex items-center justify-center text-on-surface-variant opacity-60 hover:opacity-100 hover:bg-surface-container transition-all duration-200">
                    <span className="material-symbols-outlined">account_circle</span>
                </button>
                <button className="w-full py-3 flex items-center justify-center text-on-surface-variant opacity-60 hover:opacity-100 hover:bg-surface-container transition-all duration-200">
                    <span className="material-symbols-outlined">settings</span>
                </button>
            </div>
        </aside>
    )
}
