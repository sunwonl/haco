"""
UI Engineer agent node.

Responsibilities:
- Read architecture notes to understand UI/Frontend requirements.
- Generate HTML, CSS, and Client-side JavaScript.
- Handle styling, layout, and user interaction logic.
- Write files via FileIOTool and commit via GitTool.
- Mark tasks as completed and hand control back to PO.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from harnesscore.schema import SystemState, TaskLog
from harnesscore.config.loader import HarnessConfig
from harnesscore.llm import get_llm
from harnesscore.tools.file_io import FileIOTool
from harnesscore.tools.git_tool import GitTool


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
    reasoning: str = Field(description="Reasoning for the UI implementation.")
    files: list[FileContent] = Field(description="List of UI files to create or modify.")
    resolved_task_ids: list[str] = Field(description="IDs of tasks resolved by this action.")
    commit_message: str = Field(description="Git commit message.")


def _read_arch_notes(harness_dir: Path) -> str:
    """Read architecture notes for design context."""
    arch_file = harness_dir / "arch_notes.md"
    if arch_file.exists():
        return arch_file.read_text(encoding="utf-8")
    return "No architecture notes available."


def ui_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the UI Engineer."""
    print("[UI Engineer] Creating UI components...")

    project_root = Path(config.project_root or ".").resolve()
    harness_dir = project_root / ".harness"
    file_tool = FileIOTool(project_root)

    # --- 1. Gather context ------------------------------------------------
    arch_notes = _read_arch_notes(harness_dir)
    open_tasks = {
        tid: desc
        for tid, desc in state.tasks.items()
        if tid not in state.completed_tasks
    }

    # --- 2. Call LLM -------------------------------------------------------
    llm = get_llm(config, "UI Engineer")
    structured_llm = llm.with_structured_output(UIDecision)

    context_text = (
        f"User Prompt: {state.user_prompt}\n"
        f"Open Tasks (assigned to you): {json.dumps(open_tasks, ensure_ascii=False)}\n"
        f"Already Completed Tasks: {json.dumps(state.completed_tasks, ensure_ascii=False)}\n"
        f"\n--- Architecture Notes ---\n{arch_notes}\n"
    )

    decision: UIDecision = structured_llm.invoke(
        [SystemMessage(content=UI_SYSTEM_PROMPT), HumanMessage(content=context_text)]
    )

    print(f"[UI Engineer] Writing {len(decision.files)} UI file(s)...")

    # --- 3. Write files ----------------------------------------------------
    written_paths: list[str] = []
    errors: list[str] = []

    for fc in decision.files:
        rel = fc.relative_path.lstrip("/")
        try:
            file_tool.write_file(rel, fc.content)
            written_paths.append(rel)
            print(f"[UI Engineer] ✓ Written: {rel}")
        except Exception as exc:
            errors.append(f"Failed to write '{rel}': {exc}")
            print(f"[UI Engineer] ✗ Error writing '{rel}': {exc}")

    # --- 4. Git commit (on success) ----------------------------------------
    commit_hash: Optional[str] = None
    if not errors and written_paths and config.git.auto_commit:
        try:
            git = GitTool(project_root)
            git.add(".")
            git.commit(decision.commit_message)
            commit_hash = git.log(n=1).split()[0]
            print(f"[UI Engineer] Committed UI changes: {commit_hash}")
        except Exception as exc:
            print(f"[UI Engineer] Git commit skipped: {exc}")

    # --- 5. Build return payload ------------------------------------------
    status = "SUCCESS" if not errors else "FAIL"
    latest_error = "\n".join(errors) if errors else None

    new_completed = list(state.completed_tasks)
    if status == "SUCCESS":
        new_completed += [
            tid for tid in decision.resolved_task_ids if tid not in new_completed
        ]

    log = TaskLog(
        agent_name="UI Engineer",
        action_type="UI_IMPLEMENTATION",
        details=(
            f"Written UI files: {written_paths}. "
            f"Commit: {commit_hash or 'none'}."
        ),
        status=status,
    )

    return {
        "current_assignee": "UI Engineer",
        "next_agent": "QA Evaluator" if status == "SUCCESS" else "PO",
        "completed_tasks": new_completed,
        "file_changes": list(set(state.file_changes + written_paths)),
        "latest_error": latest_error,
        "history_logs": [log],
    }
