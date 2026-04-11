"""
Core state graph orchestration using LangGraph.
"""
from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, END

from harnesscore.schema import SystemState, TaskLog
from harnesscore.config.loader import HarnessConfig
from harnesscore.agents.po import po_node
from harnesscore.agents.sa import sa_node
from harnesscore.agents.cd import cd_node


def dummy_node(agent_name: str):
    """Temporary dummy node for agents not yet implemented."""
    def _node(state: SystemState) -> dict:
        print(f"[{agent_name}] Dummy node executed.")
        log = TaskLog(
            agent_name=agent_name,
            action_type="DEBUG",
            details=f"Executed dummy node. (stub – agent not yet implemented)",
            status="SUCCESS",
        )
        # Find the first open task and mark it done so PO can make progress
        open_tasks = [tid for tid in state.tasks if tid not in state.completed_tasks]
        newly_completed = list(state.completed_tasks)
        if open_tasks:
            newly_completed.append(open_tasks[0])
            print(f"[{agent_name}] Stub: marking task '{open_tasks[0]}' as completed.")

        return {
            "current_assignee": agent_name,
            "next_agent": "PO",
            "completed_tasks": newly_completed,
            "history_logs": [log],
        }
    return _node


def build_graph(config: HarnessConfig, checkpointer: Any = None):
    """Construct and compile the main LangGraph StateGraph."""
    
    # 1. Initialize StateGraph with our Pydantic State Schema
    builder = StateGraph(SystemState)
    
    # 2. Add nodes (wrapping with the config payload trick if needed, 
    #    or using functools.partial. Since LangGraph standard is passing
    #    State directly, we can wrap our nodes to inject config).
    def wrapped_po(state: SystemState):
        return po_node(state, config)

    def wrapped_sa(state: SystemState):
        return sa_node(state, config)

    def wrapped_cd(state: SystemState):
        return cd_node(state, config)

    builder.add_node("PO", wrapped_po)
    builder.add_node("System Architect", wrapped_sa)
    builder.add_node("Core Developer", wrapped_cd)

    # Temporary stubs for remaining agents
    builder.add_node("Design Reviewer", dummy_node("Design Reviewer"))
    builder.add_node("UI Engineer", dummy_node("UI Engineer"))
    builder.add_node("QA Evaluator", dummy_node("QA Evaluator"))

    # 3. Add Edges
    # The start always goes to PO
    builder.set_entry_point("PO")
    
    # Conditional logic for routing outwards from PO
    def po_router(state: SystemState) -> str:
        # Pydantic states in LangGraph can sometimes be passed as dicts or objects
        # We handle both cases just to be safe
        next_agent = state.next_agent if hasattr(state, 'next_agent') else state.get("next_agent")
        
        if next_agent == "FINISH" or not next_agent:
            return END
        return next_agent

    builder.add_conditional_edges(
        "PO",
        po_router,
        {
            "System Architect": "System Architect",
            "Design Reviewer": "Design Reviewer",
            "Core Developer": "Core Developer",
            "UI Engineer": "UI Engineer",
            "QA Evaluator": "QA Evaluator",
            END: END
        }
    )
    
    # 4. Handoffs back to PO from workers
    builder.add_edge("System Architect", "PO")
    builder.add_edge("Design Reviewer", "PO")
    builder.add_edge("Core Developer", "PO")
    builder.add_edge("UI Engineer", "PO")
    builder.add_edge("QA Evaluator", "PO")
    
    return builder.compile(checkpointer=checkpointer)
