"""
UI Engineer agent node.
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
from harnesscore.utils.journaler import Journaler
from harnesscore.utils.prompt_manager import PromptManager


UI_SYSTEM_PROMPT = """\
You are the **UI Engineer** of an autonomous software engineering team.

Your responsibilities:
1. Review the architecture notes and user requirement for any UI/UX or Frontend tasks.
2. Generate modern, clean, and functional HTML, CSS, and JavaScript.
3. Ensure the UI is responsive and provides a good user experience.
4. Use the relative paths specified in the architecture note (e.g., 'frontend/index.html').
5. Mark each UI-related task you have implemented as resolved.

Rules:
- Output full, ready-to-use file content.
- Use Vanilla CSS and JavaScript unless specified otherwise.
- Ensure proper linking between HTML, CSS, and JS files.

Produce your response using structured output only.
"""


class FileContent(BaseModel):
    relative_path: str = Field(description="Relative path of the UI file.")
    content: str = Field(description="Full file content.")


class UIDecision(BaseModel):
    reasoning: str = Field(description="Internal technical reasoning for the UI implementation.")
    response_to_user: str = Field(
        description="A direct message to the user explaining the UI changes and design choices."
    )
    files: List[FileContent] = Field(description="List of UI files to create or modify.")
    resolved_task_ids: List[str] = Field(description="IDs of tasks resolved by this action.")
    commit_message: str = Field(description="Git commit message.")

FileContent.model_rebuild()
UIDecision.model_rebuild()


def _read_arch_notes(harness_dir: Path) -> str:
    """Read architecture notes for design context."""
    arch_file = harness_dir / "arch_notes.md"
    if arch_file.exists():
        return arch_file.read_text(encoding="utf-8")
    return "No architecture notes available."


from harnesscore.agents.base import run_agent_react_loop
from harnesscore.tools.journal import JournalTool
from harnesscore.tools.git_tool import GitTool

async def ui_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the UI Engineer."""
    project_root = Path(config.project_root or ".").resolve()
    harness_dir = project_root / ".harness"
    llm = get_llm(config, "UI Engineer")
    
    sys_prompt = UI_SYSTEM_PROMPT + PromptManager.load_custom_instructions(harness_dir, "UI Engineer")
    
    def read_arch_notes() -> str:
        """Read architecture notes for design context."""
        arch = harness_dir / "arch_notes.md"
        return arch.read_text(encoding="utf-8") if arch.exists() else "No arch notes."
        
    def write_file(relative_path: str, content: str) -> str:
        """Write UI source code content to a file."""
        file_tool = FileIOTool(project_root)
        try:
            file_tool.write_file(relative_path, content)
            return f"Successfully wrote {relative_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def read_journal(target_role: str = "System Architect", limit: int = 5) -> str:
        """Read the recent journal to understand recent goals."""
        jtool = JournalTool(harness_dir)
        return jtool.read_journal(limit=limit, role_filter=target_role)

    def submit_work(message: str, next_agent: str = "QA Evaluator", completed_task_id: str = None) -> str:
        """Final action to submit implementation."""
        return "WORK_SUBMITTED"

    def run_shell_command(command: str) -> str:
        """Run robust linux shell commands (e.g., cat, grep, ls, python) to inspect the codebase or execute scripts."""
        from harnesscore.tools.shell import ShellTool
        shell_tool = ShellTool(project_root)
        return shell_tool.run_command(command)
        
    tools = [read_arch_notes, write_file, read_journal, submit_work, run_shell_command]
    
    open_tasks = {
        tid: desc for tid, desc in state.tasks.items() if tid not in state.completed_tasks
    }
    context_str = (
        f"User Prompt: {state.user_prompt}\n"
        f"Open Tasks (assigned to you): {json.dumps(open_tasks, ensure_ascii=False)}\n"
        f"Already Completed Tasks: {json.dumps(state.completed_tasks, ensure_ascii=False)}\n"
    )

    result = await run_agent_react_loop(
        agent_name="UI Engineer", state=state, llm=llm, tools=tools, 
        sys_prompt=sys_prompt, context_str=context_str, harness_dir=harness_dir, max_loops=10
    )
    
    # Auto-commit feature
    if config.git.auto_commit and result.get("latest_error") is None:
        try:
            git = GitTool(project_root)
            git.add(".")
            git.commit("Auto-commit UI Changes via ReAct")
        except:
            pass
            
    return result
