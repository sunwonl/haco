"""
The Product Owner (Supervisor) agent node.
"""
from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from harnesscore.schema import SystemState, TaskLog
from harnesscore.config.loader import HarnessConfig
from harnesscore.llm import get_llm


PO_SYSTEM_PROMPT = """\
You are the **Product Owner (PO)** and Orchestrator of HarnessCore AI.
Your role is to act as a Supervisor for a team of autonomous software engineering agents.

You have the following team members (agents) available to you:
- **System Architect (SA)**: Researches the codebase and creates architecture/schema documentation.
- **Design Reviewer (DR)**: Validates logic and schema correctness.
- **Core Developer (CD)**: Writes and modifies backend code, and runs backend tests.
- **UI Engineer (UI)**: Writes and modifies frontend code.
- **QA Evaluator (QA)**: Runs end-to-end tests and reports bugs.

Your Job:
1. Analyze the 'user_prompt' and the current list of 'completed_tasks'.
2. Break the requirement down into simple, actionable tasks.
3. Keep track of what is done vs. what still needs to be done.
4. Route the execution to the most appropriate agent to do the NEXT piece of work.
5. If the work is entirely complete, or if you must ask the human for clarification, route to "FINISH".

You must extract your routing decision using structured outputs.
"""

class PORoutingDecision(BaseModel):
    reasoning: str = Field(description="Brief explanation of why you made this choice.")
    next_agent: str = Field(
        description="Must be exactly one of: 'System Architect', 'Design Reviewer', 'Core Developer', 'UI Engineer', 'QA Evaluator', or 'FINISH'."
    )
    new_tasks: dict[str, str] = Field(
        description="A dict of tasks. Keys are TaskIDs (e.g., 'T1'), values are descriptions. Can be empty if no new tasks.",
        default_factory=dict
    )

def po_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the Product Owner."""
    llm = get_llm(config, "PO")
    
    # We use LangChain's with_structured_output to force the schema.
    structured_llm = llm.with_structured_output(PORoutingDecision)
    
    # Build prompt context
    context = (
        f"User Prompt: {state.user_prompt}\n"
        f"Current Tasks: {json.dumps(state.tasks, ensure_ascii=False)}\n"
        f"Completed Tasks: {json.dumps(state.completed_tasks, ensure_ascii=False)}\n"
        f"Latest Error: {state.latest_error or 'None'}\n"
    )
    
    input_msgs = [
        SystemMessage(content=PO_SYSTEM_PROMPT),
        HumanMessage(content=context)
    ]
    
    print("[PO] Analyzing project state and determining routing...")
    decision: PORoutingDecision = structured_llm.invoke(input_msgs)
    
    # Update tasks if new ones were provided
    updated_tasks = dict(state.tasks)
    updated_tasks.update(decision.new_tasks)
    
    log = TaskLog(
        agent_name="PO",
        action_type="ROUTING",
        details=f"Routed to {decision.next_agent}. Reasoning: {decision.reasoning}",
        status="SUCCESS"
    )

    # Return a dict of fields to update in the SystemState
    # LangGraph will automatically update the State object.
    return {
        "current_assignee": "PO",
        "next_agent": decision.next_agent,
        "tasks": updated_tasks,
        "history_logs": [log]  # operator.add ensures this appends
    }
