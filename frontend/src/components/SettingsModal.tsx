import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useHarnessStore } from '../store/useHarnessStore'

type MCPServer = {
    name: string
    command: string
    args: string[]
}

type Skill = {
    id: string
    name: string
    content: string
}

type ConfigState = {
    model_id: string
    location: string
    project_id: string
    mcp_servers: Record<string, MCPServer[]>
    api_key_configured: boolean
}

export default function SettingsModal() {
    const isOpen = useHarnessStore(s => s.isSettingsOpen)
    const setIsOpen = useHarnessStore(s => s.setIsSettingsOpen)
    
    const [activeTab, setActiveTab] = useState<'general' | 'mcp' | 'skills'>('general')
    const [config, setConfig] = useState<ConfigState>({
        model_id: '',
        location: 'global',
        project_id: '',
        mcp_servers: {},
        api_key_configured: false
    })
    
    const [skills, setSkills] = useState<Skill[]>([])
    const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)
    const [isSaving, setIsSaving] = useState(false)
    const [message, setMessage] = useState('')

    // Form States
    const [selectedAgent, setSelectedAgent] = useState('global')
    const [newMcp, setNewMcp] = useState({ name: '', command: '', args: '' })

    useEffect(() => {
        if (isOpen) {
            // Load Config
            fetch('/api/config')
                .then(res => res.json())
                .then(data => setConfig(data))
                .catch(err => console.error('Failed to fetch config:', err))
            
            // Load Skills
            fetch('/api/skills')
                .then(res => res.json())
                .then(data => {
                    setSkills(data)
                    if (data.length > 0) setSelectedSkill(data[0])
                })
                .catch(err => console.error('Failed to fetch skills:', err))
        }
    }, [isOpen])

    const handleSaveConfig = async () => {
        setIsSaving(true)
        setMessage('')
        try {
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            })
            if (res.ok) {
                setMessage('Configuration saved!')
            }
        } catch (err) {
            setMessage('Failed to save settings.')
        } finally {
            setIsSaving(false)
        }
    }

    const handleSaveSkill = async () => {
        if (!selectedSkill) return
        setIsSaving(true)
        setMessage('')
        try {
            const res = await fetch('/api/skills', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(selectedSkill)
            })
            if (res.ok) {
                setMessage(`Skill '${selectedSkill.name}' updated!`)
                // Refresh list
                const list = await fetch('/api/skills').then(r => r.json())
                setSkills(list)
            }
        } catch (err) {
            setMessage('Failed to save skill.')
        } finally {
            setIsSaving(false)
        }
    }

    const createNewSkill = () => {
        const id = prompt("Enter skill ID (e.g. coding_standards, security_policy):")
        if (!id) return
        const newSkill = { id, name: id.replace(/_/g, ' ').toUpperCase(), content: "# New Skill Instructions\n\nAdd your guidelines here..." }
        setSkills([...skills, newSkill])
        setSelectedSkill(newSkill)
    }

    const deleteSkill = async (id: string) => {
        if (!confirm(`Are you sure you want to delete skill '${id}'?`)) return
        try {
            await fetch(`/api/skills/${id}`, { method: 'DELETE' })
            const list = await fetch('/api/skills').then(r => r.json())
            setSkills(list)
            if (selectedSkill?.id === id) setSelectedSkill(list[0] || null)
        } catch (err) {
            console.error('Failed to delete skill:', err)
        }
    }

    const addMcpServer = () => {
        if (!newMcp.name || !newMcp.command) return
        const updatedMcp = { ...config.mcp_servers }
        if (!updatedMcp[selectedAgent]) updatedMcp[selectedAgent] = []
        updatedMcp[selectedAgent].push({
            name: newMcp.name,
            command: newMcp.command,
            args: newMcp.args.split(' ').filter(a => a.trim() !== '')
        })
        setConfig({ ...config, mcp_servers: updatedMcp })
        setNewMcp({ name: '', command: '', args: '' })
    }

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsOpen(false)}
                        className="absolute inset-0 bg-background/60 backdrop-blur-md"
                    />

                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 10 }}
                        className="relative w-full max-w-4xl bg-surface-container-low rounded-3xl shadow-2xl border border-ghost-border/10 overflow-hidden flex flex-col h-[85vh]"
                    >
                        {/* Header */}
                        <div className="px-8 pt-8 pb-4 flex items-center justify-between shrink-0">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-primary/10 rounded-2xl flex items-center justify-center">
                                    <span className="material-symbols-outlined text-primary">settings</span>
                                </div>
                                <h2 className="text-xl font-black tracking-tight text-on-surface uppercase italic">Core_Control</h2>
                            </div>
                            <button onClick={() => setIsOpen(false)} className="p-2 hover:bg-surface-container-high rounded-full transition-colors text-outline">
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>

                        {/* Navigation Tabs */}
                        <div className="px-8 flex gap-8 border-b border-ghost-border/5 shrink-0 bg-surface-container-lowest/30">
                            {(['general', 'mcp', 'skills'] as const).map(tab => (
                                <button 
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`pb-4 pt-2 text-[10px] font-black tracking-[0.2em] uppercase border-b-2 transition-all ${activeTab === tab ? 'text-primary border-primary' : 'text-outline border-transparent hover:text-on-surface'}`}
                                >
                                    {tab}
                                </button>
                            ))}
                        </div>

                        {/* Main Content Area */}
                        <div className="flex-1 overflow-hidden flex">
                            {/* Scrollable Content */}
                            <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
                                {activeTab === 'general' && (
                                    <div className="max-w-xl space-y-6">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold text-outline uppercase tracking-widest pl-1">Primary LLM Engine</label>
                                            <select 
                                                value={config.model_id}
                                                onChange={e => setConfig({...config, model_id: e.target.value})}
                                                className="w-full bg-surface-container-lowest border border-ghost-border/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                                            >
                                                <option value="gemini-3.1-flash-lite-preview">Gemini 3.1 Flash Lite</option>
                                                <option value="gemini-3.1-pro-preview">Gemini 3.1 Pro</option>
                                                <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash</option>
                                            </select>
                                        </div>
                                        <div className="grid grid-cols-2 gap-6">
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-bold text-outline uppercase tracking-widest pl-1">Location</label>
                                                <input value={config.location} onChange={e => setConfig({...config, location: e.target.value})} className="w-full bg-surface-container-lowest border border-ghost-border/10 rounded-xl px-4 py-3 text-sm font-mono focus:outline-none" />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-bold text-outline uppercase tracking-widest pl-1">Project ID</label>
                                                <input value={config.project_id} onChange={e => setConfig({...config, project_id: e.target.value})} className="w-full bg-surface-container-lowest border border-ghost-border/10 rounded-xl px-4 py-3 text-sm font-mono focus:outline-none" />
                                            </div>
                                        </div>
                                        <button 
                                            onClick={handleSaveConfig} 
                                            disabled={isSaving}
                                            className="bg-primary text-on-primary px-8 py-3 rounded-2xl font-black text-[10px] tracking-widest uppercase hover:scale-105 transition-all shadow-lg shadow-primary/20 flex items-center gap-2"
                                        >
                                            {isSaving ? <span className="material-symbols-outlined animate-spin text-[16px]">sync</span> : 'Apply General Config'}
                                        </button>
                                    </div>
                                )}

                                {activeTab === 'mcp' && (
                                    <div className="space-y-8">
                                        <div className="grid grid-cols-2 gap-4">
                                            {Object.entries(config.mcp_servers).map(([agent, servers]) => (
                                                <div key={agent} className="space-y-3">
                                                    <div className="text-[9px] font-black text-primary uppercase tracking-widest bg-primary/5 px-2 py-1 rounded w-fit">{agent}</div>
                                                    {servers.map((s, idx) => (
                                                        <div key={idx} className="bg-surface-container-lowest p-4 rounded-2xl border border-ghost-border/5 flex justify-between items-start group">
                                                            <div>
                                                                <div className="text-sm font-bold">{s.name}</div>
                                                                <code className="text-[10px] text-outline">{s.command} {s.args.join(' ')}</code>
                                                            </div>
                                                            <button onClick={() => {
                                                                const up = {...config.mcp_servers}; up[agent].splice(idx, 1);
                                                                if(!up[agent].length) delete up[agent]; setConfig({...config, mcp_servers: up});
                                                            }} className="opacity-0 group-hover:opacity-100 p-1 text-error transition-opacity">
                                                                <span className="material-symbols-outlined text-sm">delete</span>
                                                            </button>
                                                        </div>
                                                    ))}
                                                </div>
                                            ))}
                                        </div>
                                        <div className="bg-surface-container p-6 rounded-3xl border border-primary/10 space-y-4 max-w-xl">
                                            <h3 className="text-[10px] font-black text-primary uppercase tracking-widest">Connect New MCP Server</h3>
                                            <div className="grid grid-cols-2 gap-4">
                                                <select value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)} className="bg-surface-container-lowest border border-ghost-border/10 rounded-xl p-3 text-xs focus:outline-none">
                                                    <option value="global">Global</option>
                                                    <option value="PO">Product Owner</option>
                                                    <option value="System Architect">System Architect</option>
                                                    <option value="Core Developer">Core Developer</option>
                                                    <option value="QA Evaluator">QA Evaluator</option>
                                                </select>
                                                <input placeholder="Server Name" value={newMcp.name} onChange={e => setNewMcp({...newMcp, name: e.target.value})} className="bg-surface-container-lowest border border-ghost-border/10 rounded-xl p-3 text-xs focus:outline-none" />
                                            </div>
                                            <input placeholder="Command (e.g. npx)" value={newMcp.command} onChange={e => setNewMcp({...newMcp, command: e.target.value})} className="w-full bg-surface-container-lowest border border-ghost-border/10 rounded-xl p-3 text-xs font-mono focus:outline-none" />
                                            <input placeholder="Args (e.g. -y @mcp/server)" value={newMcp.args} onChange={e => setNewMcp({...newMcp, args: e.target.value})} className="w-full bg-surface-container-lowest border border-ghost-border/10 rounded-xl p-3 text-xs font-mono focus:outline-none" />
                                            <button onClick={addMcpServer} className="w-full py-3 bg-primary/10 text-primary hover:bg-primary hover:text-on-primary rounded-xl font-bold text-[10px] uppercase tracking-widest transition-all">Register Server</button>
                                        </div>
                                        <button 
                                            onClick={handleSaveConfig} 
                                            disabled={isSaving}
                                            className="bg-primary text-on-primary px-8 py-3 rounded-2xl font-black text-[10px] tracking-widest uppercase hover:scale-105 transition-all shadow-lg shadow-primary/20 flex items-center gap-2"
                                        >
                                            {isSaving ? <span className="material-symbols-outlined animate-spin text-[16px]">sync</span> : 'Persist MCP Connections'}
                                        </button>
                                    </div>
                                )}

                                {activeTab === 'skills' && (
                                    <div className="flex h-full gap-8">
                                        {/* Skill List Sidebar */}
                                        <div className="w-64 space-y-2 shrink-0 border-r border-ghost-border/10 pr-4">
                                            <div className="flex items-center justify-between mb-4">
                                                <h3 className="text-[10px] font-black text-outline uppercase tracking-widest">Library</h3>
                                                <button onClick={createNewSkill} className="p-1.5 bg-primary/10 text-primary rounded-lg hover:bg-primary hover:text-on-primary transition-all">
                                                    <span className="material-symbols-outlined text-sm">add</span>
                                                </button>
                                            </div>
                                            {skills.map(s => (
                                                <div 
                                                    key={s.id} 
                                                    onClick={() => setSelectedSkill(s)}
                                                    className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${selectedSkill?.id === s.id ? 'bg-primary text-on-primary shadow-lg shadow-primary/20' : 'bg-surface-container-lowest/50 hover:bg-surface-container-highest'}`}
                                                >
                                                    <div className="flex items-center gap-2 overflow-hidden">
                                                        <span className="material-symbols-outlined text-sm shrink-0">{s.id === 'global' ? 'public' : 'psychology'}</span>
                                                        <span className="text-xs font-bold truncate tracking-tight">{s.name}</span>
                                                    </div>
                                                    {s.id !== 'global' && (
                                                        <button 
                                                            onClick={(e) => { e.stopPropagation(); deleteSkill(s.id); }}
                                                            className={`p-1 hover:bg-white/20 rounded transition-all ${selectedSkill?.id === s.id ? 'text-white/40 hover:text-white' : 'text-error/40 hover:text-error'}`}
                                                        >
                                                            <span className="material-symbols-outlined text-[14px]">delete</span>
                                                        </button>
                                                    )}
                                                </div>
                                            ))}
                                        </div>

                                        {/* Editor Area */}
                                        {selectedSkill ? (
                                            <div className="flex-1 flex flex-col gap-4 animate-in fade-in slide-in-from-right-4 duration-300">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex flex-col">
                                                        <span className="text-[9px] font-black text-primary uppercase tracking-widest mb-1">Targeting: {selectedSkill.id}</span>
                                                        <h3 className="text-lg font-black text-on-surface tracking-tight">{selectedSkill.name}</h3>
                                                    </div>
                                                    <button 
                                                        onClick={handleSaveSkill}
                                                        disabled={isSaving}
                                                        className="px-6 py-2 bg-secondary text-on-secondary rounded-xl font-black text-[10px] tracking-widest uppercase hover:scale-105 transition-all shadow-lg flex items-center gap-2"
                                                    >
                                                        {isSaving ? <span className="material-symbols-outlined animate-spin text-[16px]">sync</span> : 'Save Skill'}
                                                    </button>
                                                </div>
                                                <textarea 
                                                    value={selectedSkill.content}
                                                    onChange={e => setSelectedSkill({...selectedSkill, content: e.target.value})}
                                                    className="flex-1 w-full bg-[#0d0e12] text-white/80 p-6 rounded-2xl font-mono text-[13px] border border-white/5 focus:outline-none focus:border-primary/30 custom-scrollbar resize-none leading-relaxed"
                                                    placeholder="Type system instructions for this skill..."
                                                />
                                            </div>
                                        ) : (
                                            <div className="flex-1 flex flex-col items-center justify-center opacity-20">
                                                <span className="material-symbols-outlined text-[4rem]">auto_fix_high</span>
                                                <p className="font-mono text-sm uppercase tracking-[0.3em] mt-4">Select or Create a Skill</p>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Status Bar Footer */}
                        <div className="px-8 py-3 bg-[#111218] border-t border-white/5 flex items-center justify-between shrink-0">
                            <div className="flex items-center gap-2">
                                <span className={`w-1.5 h-1.5 rounded-full ${config.api_key_configured ? 'bg-secondary' : 'bg-error'} shadow-[0_0_8px_rgba(78,222,163,0.3)]`} />
                                <span className="text-[10px] text-white/30 font-mono tracking-wider">
                                    {config.api_key_configured ? 'AUTH_READY' : 'AUTH_REQUIRED'} • {message || 'SYSTEM_IDLE'}
                                </span>
                            </div>
                            <div className="text-[10px] text-white/20 font-mono italic uppercase tracking-widest">
                                harnesscore.config.v2
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
