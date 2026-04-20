import { ReactFlow, Controls, Background, Handle, Position } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useMemo } from 'react';
import { useHarnessStore } from '../store/useHarnessStore';

const STATUS_COLORS = {
    idle: { bg: 'bg-[#1d2026]', text: 'text-slate-400', border: 'border-slate-800' },
    thinking: { bg: 'bg-sky-900', text: 'text-sky-100', border: 'border-sky-400' },
    success: { bg: 'bg-emerald-900', text: 'text-emerald-100', border: 'border-emerald-400' },
    error: { bg: 'bg-red-950', text: 'text-red-100', border: 'border-red-500' },
};

function AgentNode({ id, data }: { id: string; data: any }) {
    const status = useHarnessStore((s) => s.nodeStatuses[id] || 'idle');
    const details = useHarnessStore((s) => s.nodeDetails[id]);
    const activeNode = useHarnessStore((s) => s.activeNode);
    const theme = STATUS_COLORS[status];
    const isActive = activeNode === id;

    return (
        <div className={`px-4 py-3 rounded-lg border shadow-xl min-w-[160px] transition-all duration-500 ${theme.bg} ${theme.border} ${isActive ? 'ring-2 ring-sky-400 ring-offset-2 ring-offset-[#0f1115] scale-105' : ''}`}>
            <Handle type="target" position={Position.Top} className="w-2 h-2 bg-slate-600 border-none" />
            <div className="flex flex-col gap-1">
                <span className={`text-xs font-bold uppercase tracking-wider ${theme.text}`}>
                    {data.label}
                </span>
                {details && (
                    <span className="text-[10px] text-slate-400 line-clamp-1 overflow-hidden">
                        {details}
                    </span>
                )}
            </div>
            <Handle type="source" position={Position.Bottom} className="w-2 h-2 bg-slate-600 border-none" />
        </div>
    );
}

const nodeTypes = {
    agent: AgentNode,
};

const initialNodes = [
    { id: 'PO', type: 'agent', position: { x: 250, y: 50 }, data: { label: 'Product Owner' } },
    { id: 'System Architect', type: 'agent', position: { x: 50, y: 150 }, data: { label: 'System Architect' } },
    { id: 'Design Reviewer', type: 'agent', position: { x: 50, y: 250 }, data: { label: 'Design Reviewer' } },
    { id: 'Core Developer', type: 'agent', position: { x: 450, y: 150 }, data: { label: 'Core Developer' } },
    { id: 'UI Engineer', type: 'agent', position: { x: 450, y: 250 }, data: { label: 'UI Engineer' } },
    { id: 'QA Evaluator', type: 'agent', position: { x: 250, y: 350 }, data: { label: 'QA Evaluator' } },
];

const staticEdges = [
    { id: 'e-po-sa', source: 'PO', target: 'System Architect' },
    { id: 'e-sa-dr', source: 'System Architect', target: 'Design Reviewer' },
    { id: 'e-dr-po', source: 'Design Reviewer', target: 'PO' },
    { id: 'e-po-cd', source: 'PO', target: 'Core Developer' },
    { id: 'e-cd-qa', source: 'Core Developer', target: 'QA Evaluator' },
    { id: 'e-po-ui', source: 'PO', target: 'UI Engineer' },
    { id: 'e-ui-qa', source: 'UI Engineer', target: 'QA Evaluator' },
    { id: 'e-qa-po', source: 'QA Evaluator', target: 'PO' },
    { id: 'e-dr-cd', source: 'Design Reviewer', target: 'Core Developer' },
];

export default function GraphCanvas() {
    const routingEdge = useHarnessStore((s) => s.routingEdge);

    const edges = useMemo(() => {
        return staticEdges.map((e) => {
            const isRouting = routingEdge?.from === e.source && routingEdge?.to === e.target;
            return {
                ...e,
                animated: isRouting,
                style: {
                    stroke: isRouting ? '#38bdf8' : '#334155',
                    strokeWidth: isRouting ? 3 : 1.5,
                    transition: 'all 0.5s ease',
                },
            };
        });
    }, [routingEdge]);

    return (
        <div className="w-full h-full bg-[#0f1115]">
            <ReactFlow
                nodes={initialNodes}
                edges={edges}
                nodeTypes={nodeTypes}
                fitView
                colorMode="dark"
                draggable={false}
                nodesConnectable={false}
                zoomOnScroll={false}
            >
                <Background gap={20} size={1} color="#1e293b" />
                <Controls />
            </ReactFlow>
        </div>
    );
}
