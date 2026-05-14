"""
Core Developer agent node.
"""
import json
from pathlib import Path
from typing import Optional, List, Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from harnesscore.schema import SystemState, TaskLog
from harnesscore.config.loader import HarnessConfig
from harnesscore.llm import get_llm, extract_token_usage
from harnesscore.tools.file_io import FileIOTool
from harnesscore.tools.git_tool import GitTool
from harnesscore.tools.shell import ShellTool
from harnesscore.utils.journaler import Journaler
from harnesscore.utils.prompt_manager import PromptManager


CD_SYSTEM_PROMPT = """\
You are the **Core Developer (CD)**, the technical craftsman of the team.
Your mission is to transform architectural designs into robust, high-quality source code.

### Your Core Responsibilities:
1. **Design Compliance**: Read the System Architect's (SA) architecture notes (`arch_notes.md`) carefully. You MUST strictly follow the specified file structure, API signatures, and logic flows.
2. **High-Quality Implementation**: Write clean, production-ready code. Every file must include appropriate docstrings, type hints (where applicable), and proper error handling.
3. **Self-Verification (Unit Testing)**: You are responsible for the first line of defense. Write unit tests (using `pytest`) for any logic you implement. Run them and ensure they pass before submitting.
4. **Focused Scope**: Do NOT modify architectural documentation or user-facing READMEs. Focus exclusively on `src/`, `tests/`, and related code assets.

### Implementation Rules:
- **No Stubs**: Never use `pass` or placeholders for core logic. Every file must be fully functional.
- **Relative Path Integrity**: Use the exact relative paths provided in the task list or arch notes.
- **Test Integrity**: Ensure tests are runnable from the project root.
- **Commit with Context**: Provide a meaningful git commit message that describes *why* the change was made, not just *what* was changed.

**Final Step**: Once you have implemented and verified your code with tests, use `submit_work` to hand over to the **QA Evaluator**.
"""


class FileContent(BaseModel):
    relative_path: str = Field(description="Relative path for this file (e.g., 'backend/calculator.py').")
    content: str = Field(description="The complete source code content for this file.")


class CDDecision(BaseModel):
    reasoning: str = Field(description="Internal technical reasoning for the implementation.")
    response_to_user: str = Field(
        description="A direct, helpful message to the user explaining what you have implemented and any tests run."
    )
    files: List[FileContent] = Field(description="List of files to write, each with its full content.")
    resolved_task_ids: List[str] = Field(
        description="IDs of tasks from the task list that this implementation has resolved."
    )
    commit_message: str = Field(description="A concise git commit message for these changes.")

FileContent.model_rebuild()
CDDecision.model_rebuild()


def _read_arch_notes(harness_dir: Path) -> str:
    """Read the latest architecture notes."""
    arch_file = harness_dir / "arch_notes.md"
    if arch_file.exists():
        return arch_file.read_text(encoding="utf-8")
    return "No architecture notes available."


from harnesscore.agents.base import run_agent_react_loop
from harnesscore.tools.journal import JournalTool
from harnesscore.tools.git_tool import GitTool

async def cd_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the Core Developer."""
    project_root = Path(config.project_root or ".").resolve()
    harness_dir = project_root / ".harness"
    llm = get_llm(config, "Core Developer")
    
    sys_prompt = CD_SYSTEM_PROMPT + PromptManager.load_custom_instructions(harness_dir, "Core Developer")
    
    def read_arch_notes() -> str:
        """Read the latest architecture notes written by System Architect."""
        arch = harness_dir / "arch_notes.md"
        return arch.read_text(encoding="utf-8") if arch.exists() else "No arch notes."
        
    def write_file(relative_path: str, content: str) -> str:
        """Write source code content to a file. Provide full file content."""
        file_tool = FileIOTool(project_root)
        try:
            file_tool.write_file(relative_path, content)
            return f"Successfully wrote {relative_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def run_tests(command: str = "python -m pytest") -> str:
        """Run tests, defaults to pytest."""
        shell_tool = ShellTool(project_root)
        return shell_tool.run_command(command)
        
    def read_journal(target_role: str = "System Architect", limit: int = 5) -> str:
        """Read the recent journal to understand what other agents have done."""
        jtool = JournalTool(harness_dir)
        return jtool.read_journal(limit=limit, role_filter=target_role)

    def submit_work(message: str, next_agent: str = "QA Evaluator", completed_task_id: str = None) -> str:
        """
        Final action to submit implementation.
        Args:
            message: Your final status message and reasoning.
            next_agent: 'QA Evaluator' usually.
            completed_task_id: ID of the task you finished.
        """
        return "WORK_SUBMITTED"

    def run_shell_command(command: str) -> str:
        """Run robust linux shell commands (e.g., cat, grep, ls, python) to inspect the codebase or execute scripts."""
        shell_tool = ShellTool(project_root)
        return shell_tool.run_command(command)
        
    tools = [read_arch_notes, write_file, run_tests, read_journal, submit_work, run_shell_command]
    
    open_tasks = {
        tid: desc for tid, desc in state.tasks.items() if tid not in state.completed_tasks
    }
    context_str = (
        f"User Prompt: {state.user_prompt}\n"
        f"Open Tasks (assigned to you): {json.dumps(open_tasks, ensure_ascii=False)}\n"
        f"Already Completed Tasks: {json.dumps(state.completed_tasks, ensure_ascii=False)}\n"
    )

    result = await run_agent_react_loop(
        agent_name="Core Developer", state=state, llm=llm, tools=tools, 
        sys_prompt=sys_prompt, context_str=context_str, harness_dir=harness_dir, max_loops=10
    )
    
    # Auto-commit feature
    if config.git.auto_commit and result["next_agent"] == "QA Evaluator":
        try:
            git = GitTool(project_root)
            git.add(".")
            git.commit("Auto-commit CD Changes via ReAct Loop")
        except:
            pass
            
    return result
