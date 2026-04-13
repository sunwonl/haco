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
Your role is to act as a Supervisor for a team of autonomous software engineering agents.

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
- If you can answer a question directly using your diagnostic information, do so and route to \"FINISH\".
- If the user needs work done, create tasks and route to the appropriate agent.
- If you need more info from the user, route to \"HUMAN\".

Response format:
You must provide 'reasoning' (your direct message to the user) and classify the 'intent'.
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


from harnesscore.utils.journaler import Journaler

def po_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the Product Owner."""
    llm = get_llm(config, "PO")
    structured_llm = llm.with_structured_output(PORoutingDecision)
    
    project_root = Path(config.project_root or ".")
    harness_dir = project_root / ".harness"
    file_tool = FileIOTool(project_root)
    shell_tool = ShellTool(project_root)

    # --- 1. Basic Environmental Awareness (Direct Diagnostics) ---
    try:
        file_structure = shell_tool.list_files_tree(depth=2)
        git_status = shell_tool.run_command("git status --short")
    except:
        file_structure = "Unknown (Error)"
        git_status = "Unknown (Error)"

    # --- 2. Construct context ---
    # Smart context loading: Read arch_notes if user asks about design/app status
    query = state.user_prompt.lower()
    design_context = ""
    if any(k in query for k in ["내용", "기억", "설계", "디자인", "아키텍처", "상태", "status", "design", "arch"]):
        # Read Architecture Notes (Planner context)
        arch_file = harness_dir / "arch_notes.md"
        if arch_file.exists():
            try:
                design_context += f"\n--- Current Design (arch_notes.md) ---\n{arch_file.read_text(encoding='utf-8')}\n"
            except:
                pass
        
        # Read Implementation Notes (Generator context)
        dev_file = harness_dir / "dev_notes.md"
        if dev_file.exists():
            try:
                design_context += f"\n--- Current Implementation (dev_notes.md) ---\n{dev_file.read_text(encoding='utf-8')}\n"
            except:
                pass

        # Read Project Manifests (README, etc.)
        for doc_name in ["README.md", "pyproject.toml", "package.json"]:
            doc_path = project_root / doc_name
            if doc_path.exists():
                try:
                    # Read first 2000 chars to avoid prompt bloat
                    content = doc_path.read_text(encoding="utf-8")[:2000]
                    design_context += f"\n--- Project {doc_name} ---\n{content}\n"
                except:
                    pass

    context_lines = [
        f"User Prompt: {state.user_prompt}",
        f"Project Structure:\n{file_structure}",
        f"Git Status:\n{git_status}",
        f"Tasks: {json.dumps(state.tasks, ensure_ascii=False)}",
        f"Completed: {json.dumps(state.completed_tasks, ensure_ascii=False)}",
        design_context
    ]
    
    if state.history_logs:
        recent = "\n".join([f"- {l.agent_name}: {l.details}" for l in state.history_logs[-5:]])
        context_lines.append(f"Recent History:\n{recent}")

    # --- 3. Call LLM ---
    print(f"[PO] Analyzing with diagnostic context...")
    
    # Load custom instructions
    custom_instr = PromptManager.load_custom_instructions(harness_dir, "PO")
    
    decision: PORoutingDecision = structured_llm.invoke([
        SystemMessage(content=PO_SYSTEM_PROMPT + custom_instr),
        HumanMessage(content="\n".join(context_lines))
    ])
    
    updated_tasks = dict(state.tasks)
    updated_tasks.update(decision.new_tasks)
    
    action_type = f"ORCHESTRATION_{decision.intent}"
    if decision.next_agent == "FINISH":
        action_type = "MESSAGE"
        
    log = TaskLog(
        agent_name="PO",
        action_type=action_type,
        details=decision.response,
        logs=f"Reasoning: {decision.reasoning}",
        status="SUCCESS"
    )

    # Explicit Journaling
    Journaler.log_activity(
        harness_dir=harness_dir,
        thread_id=getattr(state, "thread_id", "unknown"),
        log_data=log.model_dump(),
        language=config.language
    )

    return {
        "current_assignee": "PO",
        "next_agent": decision.next_agent,
        "tasks": updated_tasks,
        "history_logs": [log],
        "messages": [
            {"role": "user", "content": state.user_prompt},
            {"role": "assistant", "content": decision.response}
        ]
    }
