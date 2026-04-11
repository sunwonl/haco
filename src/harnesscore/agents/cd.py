"""
Core Developer agent node.

Responsibilities:
- Read the architecture notes produced by the System Architect.
- Generate actual implementation code for the assigned tasks.
- Write files to the project using FileIOTool (Path Guard enforced).
- Run pytest and capture results.
- Stage & commit changes via GitTool.
- Mark tasks as completed and surface any errors back to PO.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from harnesscore.schema import SystemState, TaskLog
from harnesscore.config.loader import HarnessConfig
from harnesscore.llm import get_llm
from harnesscore.tools.file_io import FileIOTool
from harnesscore.tools.git_tool import GitTool


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
    reasoning: str = Field(description="Brief explanation of the implementation decisions made.")
    files: list[FileContent] = Field(description="List of files to write, each with its full content.")
    resolved_task_ids: list[str] = Field(
        description="IDs of tasks from the task list that this implementation has resolved."
    )
    commit_message: str = Field(description="A concise git commit message for these changes.")


def _read_arch_notes(harness_dir: Path) -> str:
    """Read the latest architecture notes."""
    arch_file = harness_dir / "arch_notes.md"
    if arch_file.exists():
        return arch_file.read_text(encoding="utf-8")
    return "No architecture notes available."


def _run_pytest(project_root: Path, timeout: int = 60) -> tuple[bool, str]:
    """
    Run pytest from project_root.
    Returns (passed: bool, output: str).
    """
    result = subprocess.run(
        ["python", "-m", "pytest", "--tb=short", "-q"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = result.stdout + result.stderr
    passed = result.returncode == 0
    return passed, output


def cd_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the Core Developer."""
    print("[Core Developer] Starting implementation...")

    project_root = Path(config.project_root or ".").resolve()
    harness_dir = project_root / ".harness"
    file_tool = FileIOTool(project_root)

    # Determine the allowed root directory for file writes (Path Guard)
    agent_root = config.agent_paths.get("Core Developer")
    write_root = project_root / agent_root if agent_root else project_root

    # --- 1. Gather context ------------------------------------------------
    arch_notes = _read_arch_notes(harness_dir)
    open_tasks = {
        tid: desc
        for tid, desc in state.tasks.items()
        if tid not in state.completed_tasks
    }

    # --- 2. Call LLM -------------------------------------------------------
    llm = get_llm(config, "Core Developer")
    structured_llm = llm.with_structured_output(CDDecision)

    context_text = (
        f"User Prompt: {state.user_prompt}\n"
        f"Open Tasks (assigned to you): {json.dumps(open_tasks, ensure_ascii=False)}\n"
        f"Already Completed Tasks: {json.dumps(state.completed_tasks, ensure_ascii=False)}\n"
        f"\n--- Architecture Notes ---\n{arch_notes}\n"
    )

    decision: CDDecision = structured_llm.invoke(
        [SystemMessage(content=CD_SYSTEM_PROMPT), HumanMessage(content=context_text)]
    )

    print(f"[Core Developer] Writing {len(decision.files)} file(s)...")

    # --- 3. Write files ----------------------------------------------------
    written_paths: list[str] = []
    errors: list[str] = []

    for fc in decision.files:
        rel = fc.relative_path.lstrip("/")
        try:
            file_tool.write_file(rel, fc.content)
            written_paths.append(rel)
            print(f"[Core Developer] ✓ Written: {rel}")
        except Exception as exc:
            errors.append(f"Failed to write '{rel}': {exc}")
            print(f"[Core Developer] ✗ Error writing '{rel}': {exc}")

    # --- 4. Run tests ------------------------------------------------------
    test_passed, test_output = _run_pytest(project_root)
    print(f"[Core Developer] Tests: {'PASSED' if test_passed else 'FAILED'}")
    if not test_passed:
        print(f"[Core Developer] Test output:\n{test_output[:500]}")

    # --- 5. Git commit (only on test pass) ---------------------------------
    commit_hash: Optional[str] = None
    if test_passed and written_paths and config.git.auto_commit:
        try:
            git = GitTool(project_root)
            git.add(".")
            git.commit(decision.commit_message)
            commit_hash = git.log(n=1).split()[0]
            print(f"[Core Developer] Committed: {commit_hash}")
        except Exception as exc:
            print(f"[Core Developer] Git commit skipped: {exc}")

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
        details=(
            f"Written: {written_paths}. "
            f"Tests: {'passed' if test_passed else 'failed'}. "
            f"Commit: {commit_hash or 'none'}."
        ),
        status=status,
    )

    return {
        "current_assignee": "Core Developer",
        "next_agent": "QA Evaluator" if test_passed else "PO",
        "completed_tasks": new_completed,
        "file_changes": list(set(state.file_changes + written_paths)),
        "latest_error": latest_error,
        "history_logs": [log],
    }
