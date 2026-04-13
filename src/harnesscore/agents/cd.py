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
You are the **Core Developer (CD)** of an autonomous software engineering team.

Your responsibilities:
1. Read the architecture notes provided to understand *what* to build and *where*.
2. Generate complete, working source code for every file listed in the architecture note.
3. For each file, output the full content – no stubs, no placeholder comments.
4. Follow existing project conventions (language, import style, etc.) revealed by the codebase snippets.
5. Mark each task you have fully implemented as resolved.

Rules:
- Never output partial code. Every file must be runnable as-is.
- Always include a `if __name__ == '__main__':` block in scripts when appropriate.
- Use the **relative paths** specified in the architecture note exactly as given.
- Tests must be written so they can be executed with `pytest` from the project root.

Produce your response using structured output only.
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


def cd_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the Core Developer."""
    print("[Core Developer] Starting implementation...")

    project_root = Path(config.project_root or ".").resolve()
    harness_dir = project_root / ".harness"
    file_tool = FileIOTool(project_root)
    shell_tool = ShellTool(project_root)

    # --- 1. Gather context ------------------------------------------------
    arch_notes = _read_arch_notes(harness_dir)
    open_tasks = {
        tid: desc
        for tid, desc in state.tasks.items()
        if tid not in state.completed_tasks
    }

    # --- 2. Call LLM -------------------------------------------------------
    llm = get_llm(config, "Core Developer")
    structured_llm = llm.with_structured_output(CDDecision, include_raw=True)

    context_text = (
        f"User Prompt: {state.user_prompt}\n"
        f"Open Tasks (assigned to you): {json.dumps(open_tasks, ensure_ascii=False)}\n"
        f"Already Completed Tasks: {json.dumps(state.completed_tasks, ensure_ascii=False)}\n"
        f"\n--- Architecture Notes ---\n{arch_notes}\n"
    )

    print("[Core Developer] Calling LLM for implementation code...")
    
    # Load custom instructions
    custom_instr = PromptManager.load_custom_instructions(harness_dir, "Core Developer")
    
    raw_result = structured_llm.invoke(
        [SystemMessage(content=CD_SYSTEM_PROMPT + custom_instr), HumanMessage(content=context_text)]
    )
    
    decision: CDDecision = raw_result["parsed"]
    raw_resp = raw_result["raw"]
    
    # Extract token usage
    tokens = extract_token_usage(raw_resp)

    print(f"[Core Developer] Writing {len(decision.files)} file(s)...")

    # --- 3. Write files ----------------------------------------------------
    written_paths: list[str] = []
    errors: list[str] = []

    for fc in decision.files:
        rel = fc.relative_path.lstrip("/")
        try:
            file_tool.write_file(rel, fc.content)
            written_paths.append(rel)
        except Exception as exc:
            errors.append(f"Failed to write '{rel}': {exc}")

    # --- 4. Run tests using ShellTool --------------------------------------
    print("[Core Developer] Running tests via ShellTool...")
    test_output = shell_tool.run_command("python -m pytest --tb=short -q")
    test_passed = "Failed" not in test_output and "Error" not in test_output
    print(f"[Core Developer] Tests: {'PASSED' if test_passed else 'FAILED'}")

    # --- 5. Git commit (only on test pass) ---------------------------------
    commit_hash: Optional[str] = None
    if test_passed and written_paths and config.git.auto_commit:
        try:
            git = GitTool(project_root)
            git.add(".")
            git.commit(decision.commit_message)
            commit_hash = git.log(n=1).split()[0]
        except Exception as exc:
            errors.append(f"Git commit failed: {exc}")

    # --- 6. Build return payload ------------------------------------------
    latest_error: Optional[str] = None
    status = "SUCCESS"

    if errors:
        latest_error = "\n".join(errors)
        status = "FAIL"
    elif not test_passed:
        latest_error = f"Tests failed:\n{test_output[:800]}"
        status = "FAIL"

    new_completed = list(state.completed_tasks)
    if status == "SUCCESS":
        new_completed += [
            tid for tid in decision.resolved_task_ids if tid not in new_completed
        ]

    log = TaskLog(
        agent_name="Core Developer",
        action_type="IMPLEMENTATION",
        input_context=context_text,
        details=decision.response_to_user,
        logs=(
            f"Reasoning: {decision.reasoning}\n"
            f"Written: {written_paths}\n"
            f"Test Output:\n{test_output}\n"
            f"Commit: {commit_hash or 'none'}"
        ),
        status=status,
        tokens=tokens
    )

    # Write implementation notes (Generator Scratchpad)
    try:
        dev_notes_path = config.harness_dir / "dev_notes.md"
        dev_notes_path.write_text(
            f"# Core Developer Implementation Notes\n\n"
            f"**Last Action**: {decision.response_to_user}\n\n"
            f"**Technical Reasoning**:\n{decision.reasoning}\n",
            encoding="utf-8"
        )
    except:
        pass

    # Explicit Journaling
    Journaler.log_activity(
        harness_dir=config.harness_dir,
        thread_id=getattr(state, "thread_id", "unknown"),
        log_data=log.model_dump(),
        language=config.language
    )

    return {
        "current_assignee": "Core Developer",
        "next_agent": "QA Evaluator" if test_passed else "PO",
        "completed_tasks": new_completed,
        "file_changes": list(set(state.file_changes + written_paths)),
        "latest_error": latest_error,
        "history_logs": [log],
    }
