import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from harnesscore.graph import build_graph
from harnesscore.config.loader import load_config
from harnesscore.schema import SystemState

def test_hitl_points():
    config = load_config()
    graph = build_graph(config)
    
    # We check the 'interrupt_before' nodes in the compiled graph
    # LangGraph exposes this in the internal 'nodes' or 'interrupt_before' attribute
    # In recent versions, it's often in 'compiled_graph.interrupt_before'
    # LangGraph CompiledStateGraph exposes this as 'interrupt_before_nodes'
    interrupts = getattr(graph, "interrupt_before_nodes", [])
    print(f"Nodes triggering interrupt: {interrupts}")
    
    assert "PO" not in interrupts
    assert "Design Reviewer" in interrupts
    assert "Core Developer" in interrupts
    
    print("HITL Policy Verification: SUCCESS")

if __name__ == "__main__":
    test_hitl_points()
