import { ReactFlow, Controls, Background, useNodesState, useEdgesState } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useEffect } from 'react';

const initialNodes = [
    { id: 'PO', position: { x: 250, y: 50 }, data: { label: 'Product Owner' } },
    { id: 'System Architect', position: { x: 50, y: 150 }, data: { label: 'System Architect' } },
    { id: 'Design Reviewer', position: { x: 50, y: 250 }, data: { label: 'Design Reviewer' } },
    { id: 'Core Developer', position: { x: 450, y: 150 }, data: { label: 'Core Developer' } },
    { id: 'UI Engineer', position: { x: 450, y: 250 }, data: { label: 'UI Engineer' } },
    { id: 'QA Evaluator', position: { x: 250, y: 350 }, data: { label: 'QA Evaluator' } },
];

const initialEdges = [
    { id: 'e1', source: 'PO', target: 'System Architect', animated: true },
    { id: 'e2', source: 'System Architect', target: 'Design Reviewer' },
    { id: 'e3', source: 'Design Reviewer', target: 'PO' },
    { id: 'e4', source: 'PO', target: 'Core Developer', animated: true },
    { id: 'e5', source: 'Core Developer', target: 'QA Evaluator' },
    { id: 'e6', source: 'PO', target: 'UI Engineer', animated: true },
    { id: 'e7', source: 'UI Engineer', target: 'QA Evaluator' },
    { id: 'e8', source: 'QA Evaluator', target: 'PO' },
];

export default function GraphCanvas({ activeNode }: { activeNode: string | null }) {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, , onEdgesChange] = useEdgesState(initialEdges);

    useEffect(() => {
        setNodes((nds) =>
            nds.map((n) => ({
                ...n,
                style: {
                    background: n.id === activeNode ? '#0ea5e9' : '#1d2026',
                    color: n.id === activeNode ? '#00344d' : '#e1e2eb',
                    border: '1px solid rgba(62, 72, 80, 0.15)',
                    borderRadius: '0.375rem',
                    padding: '12px 20px',
                    fontWeight: n.id === activeNode ? 'bold' : 'normal',
                    boxShadow: n.id === activeNode ? '0 0 15px rgba(14, 165, 233, 0.4)' : '0 16px 32px rgba(0, 0, 0, 0.4)',
                    transition: 'all 0.3s ease'
                },
            }))
        );
    }, [activeNode, setNodes]);

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                fitView
                colorMode="dark"
            >
                <Background gap={16} size={1} color="#334155" />
                <Controls />
            </ReactFlow>
        </div>
    );
}
