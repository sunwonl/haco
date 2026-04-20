"""
The Design Reviewer (DR) agent node.
Responsible for validating architecture and schema designs before implementation.
"""
import json
from pathlib import Path
from typing import Literal, Dict, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from harnesscore.schema import SystemState, TaskLog
from harnesscore.config.loader import HarnessConfig
from harnesscore.llm import get_llm
from harnesscore.tools.validation import ValidationTool
from harnesscore.tools.file_io import FileIOTool
from harnesscore.utils.journaler import Journaler
from harnesscore.utils.prompt_manager import PromptManager


DR_SYSTEM_PROMPT = """\
You are the **Design Reviewer (DR)**. Your role is to serve as the quality gate between System Architecture and Implementation.

### Your Responsibilities:
1. **Architecture Review**: Examine the `arch_notes.md` produced by the System Architect.
2. **Implementation Readiness**: Verify if the SA's documentation is specific enough (file paths, class/function signatures, API contracts) for the Core Developer (CD) to implement without guessing.
3. **Schema Validation**: Ensure Pydantic/SQLAlchemy models are logically sound.
4. **Consistency**: Verify alignment with the original user requirement and project conventions.

### Your Verdict:
- **PASS**: The design is sound, consistent, and **immediately actionable** by CD.
- **REVISE**: The design has flaws or is too vague. Provide specific feedback for the SA to fix.

You must be rigorous and technical. Do not let vague designs through to the implementation phase.
"""

class DRDecision(BaseModel):
    reasoning: str = Field(description="Internal technical analysis of the design.")
    feedback: str = Field(description="Direct message/feedback to the System Architect or User.")
    verdict: Literal["PASS", "REVISE"] = Field(description="Whether to proceed or return for revision.")

DRDecision.model_rebuild()


from harnesscore.agents.base import run_agent_react_loop
from harnesscore.tools.journal import JournalTool

def dr_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the Design Reviewer."""
    project_root = Path(config.project_root or ".")
    harness_dir = project_root / ".harness"
    llm = get_llm(config, "Design Reviewer")
    
    sys_prompt = DR_SYSTEM_PROMPT + PromptManager.load_custom_instructions(harness_dir, "Design Reviewer")
    
    def read_arch_notes() -> str:
        """Read architecture notes for design context."""
        arch = harness_dir / "arch_notes.md"
        return arch.read_text(encoding="utf-8") if arch.exists() else "Error: Architecture notes file missing."

    def check_architecture_sync() -> str:
        """Check if tests and architectural spec are synced."""
        val_tool = ValidationTool(project_root)
        try:
            return val_tool.check_architecture_sync()
        except Exception as e:
            return f"Error: {e}"
        
    def validate_schema(file_path: str) -> str:
        """Validate if a python schema file is well-formed statically."""
        val_tool = ValidationTool(project_root)
        try:
            return val_tool.validate_schema(file_path)
        except Exception as e:
            return f"Error: {e}"

    def read_journal(target_role: str = "System Architect", limit: int = 5) -> str:
        """Read what the System Architect designed."""
        jtool = JournalTool(harness_dir)
        return jtool.read_journal(limit=limit, role_filter=target_role)

    def submit_review(verdict: Literal["PASS", "REVISE"], message: str, next_agent: str = "System Architect", completed_task_id: str = None) -> str:
        """
        Submit the review verdict. 
        If passing, set next_agent to 'Core Developer'.
        If revise, set next_agent to 'System Architect'.
        """
        return "WORK_SUBMITTED"

    def run_shell_command(command: str) -> str:
        """Run robust linux shell commands (e.g., cat, grep, ls, python) to inspect the codebase or execute scripts."""
        from harnesscore.tools.shell import ShellTool
        shell_tool = ShellTool(project_root)
        return shell_tool.run_command(command)

    tools = [read_arch_notes, check_architecture_sync, validate_schema, read_journal, submit_review, run_shell_command]
    
    context_str = (
        f"User Prompt: {state.user_prompt}\n"
    )

    result = run_agent_react_loop(
        agent_name="Design Reviewer", state=state, llm=llm, tools=tools, 
        sys_prompt=sys_prompt, context_str=context_str, harness_dir=harness_dir, max_loops=10
    )
    
    # Evaluate returning properties based on review
    last_msg = ""
    for j in result["journal"]:
        if j.category == "Message":
            last_msg = j.content.upper()
            
    if "REVISE" in last_msg or "REVISE" in result.get("next_agent", "").upper() or result.get("next_agent") == "System Architect":
        result["latest_error"] = last_msg
        result["next_agent"] = "System Architect"
    else:
        result["next_agent"] = "Core Developer"
        
    return result
