import sys
from pathlib import Path
import uuid
from langgraph.checkpoint.memory import MemorySaver

# Add src to sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from harnesscore.graph import build_graph
from harnesscore.config.loader import load_config
from harnesscore.schema import SystemState

def test_hitl_stream():
    config = load_config()
    # Provide a memory checkpointer
    checkpointer = MemorySaver()
    graph = build_graph(config, checkpointer=checkpointer)
    
    thread_id = str(uuid.uuid4())
    config_dict = {"configurable": {"thread_id": thread_id}}
    
    # 1. Test INQUIRY (Should NOT interrupt)
    print("Testing INQUIRY (should not interrupt)...")
    state_inquiry = SystemState(user_prompt="Hello, who are you?")
    
    for s in graph.stream(state_inquiry, config_dict):
        node_name = list(s.keys())[0]
        print(f"  Step: {node_name}")
    
    snapshot = graph.get_state(config_dict)
    print(f"  Next nodes: {snapshot.next}")
    assert not snapshot.next, f"Inquiry should have finished without interrupt, but got {snapshot.next}"

    # 2. Test IMPLEMENTATION (Should interrupt before Design Reviewer or CD)
    print("\nTesting IMPLEMENTATION (should interrupt before DR/CD)...")
    state_impl = SystemState(user_prompt="Create a tool for calculating Fibonacci series.")
    
    thread_id_2 = str(uuid.uuid4())
    config_dict_2 = {"configurable": {"thread_id": thread_id_2}}
    
    # This should stop before Design Reviewer or Core Developer
    for s in graph.stream(state_impl, config_dict_2):
        node_name = list(s.keys())[0]
        print(f"  Step: {node_name}")
    
    snapshot_2 = graph.get_state(config_dict_2)
    print(f"  Interrupt at: {snapshot_2.next}")
    assert snapshot_2.next, "Implementation should have reached an interrupt point"
    assert any(n in ["Design Reviewer", "Core Developer", "UI Engineer"] for n in snapshot_2.next)

    print("\nHITL Stream Verification: SUCCESS")

if __name__ == "__main__":
    test_hitl_stream()
