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
    structured_llm = llm.with_structured_output(UIDecision, include_raw=True)

    context_text = (
        f"User Prompt: {state.user_prompt}\n"
        f"Open Tasks (assigned to you): {json.dumps(open_tasks, ensure_ascii=False)}\n"
        f"Already Completed Tasks: {json.dumps(state.completed_tasks, ensure_ascii=False)}\n"
        f"\n--- Architecture Notes ---\n{arch_notes}\n"
    )

    print("[UI Engineer] Calling LLM for UI components...")
    
    # Load custom instructions
    custom_instr = PromptManager.load_custom_instructions(harness_dir, "UI Engineer")
    
    raw_result = structured_llm.invoke(
        [SystemMessage(content=UI_SYSTEM_PROMPT + custom_instr), HumanMessage(content=context_text)]
    )
    
    decision: UIDecision = raw_result["parsed"]
    raw_resp = raw_result["raw"]
    
    # Extract token usage
    tokens = extract_token_usage(raw_resp)

    print(f"[UI Engineer] Writing {len(decision.files)} UI file(s)...")

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

    # --- 4. Git commit (on success) ----------------------------------------
    commit_hash: Optional[str] = None
    if not errors and written_paths and config.git.auto_commit:
        try:
            git = GitTool(project_root)
            git.add(".")
            git.commit(decision.commit_message)
            commit_hash = git.log(n=1).split()[0]
        except Exception as exc:
            errors.append(f"Git commit failed: {exc}")

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
        input_context=context_text,
        details=decision.response_to_user,
        logs=(
            f"Reasoning: {decision.reasoning}\n"
            f"Files: {written_paths}\n"
            f"Commit: {commit_hash or 'none'}"
        ),
        status=status,
        tokens=tokens
    )

    # Explicit Journaling
    Journaler.log_activity(
        harness_dir=config.harness_dir,
        thread_id=getattr(state, "thread_id", "unknown"),
        log_data=log.model_dump(),
        language=config.language
    )

    return {
        "current_assignee": "UI Engineer",
        "next_agent": "QA Evaluator" if status == "SUCCESS" else "PO",
        "completed_tasks": new_completed,
        "file_changes": list(set(state.file_changes + written_paths)),
        "latest_error": latest_error,
        "history_logs": [log],
    }
