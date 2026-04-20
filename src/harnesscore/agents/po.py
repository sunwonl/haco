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
You are the **Product Owner (PO)** and Orchestrator of HarnessCore AI.

### Team Roles & Documentation Ownership:
- **Product Owner (PO)**: Orchestration and **User-Facing Documentation** (`README.md`, `ROADMAP.md`).
- **System Architect (SA)**: Technical Blueprint (`arch_notes.md`, `SYSTEM_ARCHITECTURE.md`).
- **Design Reviewer (DR)**: Logic/Spec Validator and Gatekeeper.
- **Core Developer (CD)**: Implementation Specialist (**Source Code and Tests only**).
- **UI Engineer (UI)**: Frontend/Visual implementation.
- **QA Evaluator (QA)**: Integration/E2E testing.

### Your Capabilities:
- You can directly inspect the project structure and environment status to answer user questions.
- You break down complex requirements into tasks and route them to specialized agents.

### Core Intent Classification:
1. **CONVERSATION**: Simple greetings or general meta-discussion.
2. **INQUIRY**: Questions about the codebase, file lists, or environment status.
   - You should try to answer simple inquiries (like "list files") yourself using your tools.
   - For deep code analysis, route to "System Architect".
3. **IMPLEMENTATION**: Requests to modify code or build features. Route through SA -> CD -> QA.

### Rules:
- **Work-Flow Awareness**: You operate in a **Sequential/Synchronous** system. Agents do NOT run in parallel while you talk to the user.
- **Honest Communication**: NEVER say 'QA is currently testing' or 'The developer is working'. Instead, say 'I will now assign this to QA' or 'I am handing over to the Architect'.
- **Global Memory Capability**: If the user explicitly states a preference, global rule, or personal fact (e.g., "Always use TypeScript", "From now on, test with pytest"), you must use the `add_memory` tool to save it permanently so all agents can remember it across sessions.
- If you can answer a question directly using your diagnostic information, do so and route to "FINISH".
- If the user needs work done, create tasks and route to the appropriate agent via `route_tasks`.
- If you need more info from the user or want to answer them, route to "HUMAN" via `route_tasks`.

**CRITICAL RULE**: You MUST use the `route_tasks` tool to conclude your turn and reply to the user. Do not just output text! If you do not use `route_tasks`, the cycle will fail.
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

def po_node(state: SystemState, config: HarnessConfig) -> dict:
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

    return run_agent_react_loop(
        agent_name="PO", state=state, llm=llm, tools=tools, 
        sys_prompt=sys_prompt, context_str=context_str, harness_dir=harness_dir, max_loops=15
    )
