"""
The Product Owner (Supervisor) agent node.
"""
import json
from pathlib import Path
from typing import Literal, Dict, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from harnesscore.schema import SystemState, TaskLog
from harnesscore.config.loader import HarnessConfig
from harnesscore.llm import get_llm
from harnesscore.tools.file_io import FileIOTool
from harnesscore.tools.shell import ShellTool
from harnesscore.utils.prompt_manager import PromptManager


PO_SYSTEM_PROMPT = """\
You are the **Product Owner (PO)** and the Strategic Orchestrator of HarnessCore AI.
Your goal is to bridge the gap between user intent and technical execution.

### Your Core Responsibilities:
1. **Requirement Refinement**: Analyze the user's prompt. If it is vague or underspecified, ask clarifying questions before assigning tasks. 
2. **Task Decomposition & Definition**: Break down requirements into clear, actionable tasks. For each task, you MUST define **Clear Success Criteria**.
3. **Orchestration**: Route tasks to the specialized agents (SA -> CD -> QA). You are the gatekeeper of the final delivery.
4. **User-Facing Documentation**: Maintain `README.md` and `ROADMAP.md` to reflect the current state and future goals of the project.
5. **Knowledge Management**: Use the `add_memory` tool to save any user preferences, global rules, or project context that should persist across sessions. If the user says "Always use X" or "I prefer Y", record it immediately.

### Workflow & Communication Guidelines:
- **Be the User's Advocate**: Ensure that the final result truly solves the user's problem, not just fulfills a technical check.
- **Strategic Handover**: When routing to the System Architect (SA), provide the full business context so they can design a better architecture.
- **Honest Communication**: Never say 'QA is currently testing'. Instead, say 'I am now assigning this to the QA team for verification' or 'I need more information about X before we proceed'.
- **Final Summary**: When a cycle is finished, summarize what was achieved in terms of **User Value**, not just a list of files changed.

**CRITICAL RULE**: You MUST use the `route_tasks` tool to conclude your turn. Do not just output text! If the user's request is a simple greeting or inquiry you can answer directly, do so within the `response_to_user` field and route to "FINISH" or "HUMAN".
"""

class PORoutingDecision(BaseModel):
    intent: Literal["CONVERSATION", "INQUIRY", "IMPLEMENTATION"] = Field(
        description="Classify the user's primary goal."
    )
    reasoning: str = Field(description="Your internal thinking process and strategy analysis.")
    response: str = Field(description="Your direct, helpful message to the user.")
    next_agent: Literal[
        "System Architect",
        "Design Reviewer",
        "Core Developer",
        "UI Engineer",
        "QA Evaluator",
        "HUMAN",
        "FINISH"
    ] = Field(
        description="Must be one of the specified agent roles, 'HUMAN', or 'FINISH'."
    )
    new_tasks: Dict[str, str] = Field(
        description="New tasks to add to the board.",
        default_factory=dict
    )

PORoutingDecision.model_rebuild()


import uuid
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from harnesscore.schema import JournalEntry, TokenUsage
from harnesscore.utils.journaler import Journaler
from harnesscore.tools.journal import JournalTool

def _ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def _extract_tokens(response) -> TokenUsage:
    meta = getattr(response, "usage_metadata", {})
    if not meta:
        return TokenUsage()
    return TokenUsage(
        input_tokens=meta.get("input_tokens", 0),
        output_tokens=meta.get("output_tokens", 0),
        thinking_tokens=meta.get("thinking_tokens", 0) # Placeholder if API ever supports it
    )

from harnesscore.agents.base import run_agent_react_loop

async def po_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution using a native Tool Calling loop for PO."""
    project_root = Path(config.project_root or ".")
    harness_dir = project_root / ".harness"
    llm = get_llm(config, "PO")

    # --- 1. Define Tools explicitly for PO ---
    def read_journal(target_role: str = "QA Evaluator", limit: int = 5) -> str:
        """Read the recent journal to understand what other agents have done."""
        jtool = JournalTool(harness_dir)
        return jtool.read_journal(limit=limit, role_filter=target_role)

    def route_tasks(next_agent: str, response: str, new_tasks: str = "{}") -> str:
        """
        Final action to route work to the next agent or finish.
        Args:
            next_agent: one of 'System Architect', 'Core Developer', 'QA Evaluator', 'UI Engineer', 'HUMAN', 'FINISH'.
            response: Your message directed to the next_agent or user.
            new_tasks: JSON string of new tasks e.g. {"T1": "Fix bug"}.
        """
        return "ROUTED"
        
    def list_files_tree(depth: int = 2) -> str:
        """List files in the project."""
        shell_tool = ShellTool(project_root)
        return shell_tool.list_files_tree(depth)

    def run_shell_command(command: str) -> str:
        """Run robust linux shell commands (e.g., cat, grep, ls, python) to inspect the codebase or execute scripts."""
        shell_tool = ShellTool(project_root)
        return shell_tool.run_command(command)

    def add_memory(fact: str) -> str:
        """Save a specific user preference, structural rule, or important context to global long-term memory."""
        from harnesscore.tools.memory import MemoryTool
        mem_tool = MemoryTool(harness_dir)
        return mem_tool.add_memory(fact)

    tools = [read_journal, route_tasks, list_files_tree, run_shell_command, add_memory]


    # --- 2. Construct context ---
    custom_instr = PromptManager.load_custom_instructions(harness_dir, "PO")
    sys_prompt = PO_SYSTEM_PROMPT + custom_instr
    
    context_str = (
        f"User Prompt: {state.user_prompt}\n"
        f"Tasks: {json.dumps(state.tasks, ensure_ascii=False)}\n"
        f"Completed Tasks: {json.dumps(state.completed_tasks, ensure_ascii=False)}\n"
        f"Latest Error: {state.latest_error or 'None'}\n"
    )

    return await run_agent_react_loop(
        agent_name="PO", state=state, llm=llm, tools=tools, 
        sys_prompt=sys_prompt, context_str=context_str, harness_dir=harness_dir, max_loops=15
    )
