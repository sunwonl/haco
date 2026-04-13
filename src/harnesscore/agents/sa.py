"""
System Architect agent node.
"""
import json
from pathlib import Path
from typing import List, Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from harnesscore.schema import SystemState, TaskLog
from harnesscore.config.loader import HarnessConfig
from harnesscore.llm import get_llm, extract_token_usage
from harnesscore.utils.journaler import Journaler
from harnesscore.utils.prompt_manager import PromptManager
from harnesscore.tools.file_io import FileIOTool


SA_SYSTEM_PROMPT = """\
You are the **System Architect (SA)** of an autonomous software engineering team.

Your responsibilities:
1. Analyze the codebase and the assigned task(s) to understand the current design.
2. Produce a concise architectural decision or design note that will guide the developer agents.
3. Identify which source files will need to be created or modified.
4. Mark every assigned task you have resolved as completed.

You have the following context available:
- user_prompt: The original user requirement.
- tasks: All tasks assigned by the PO.
- completed_tasks: Tasks already finished.
- codebase_context: Relevant files and snippets found by a prior search.

Always be helpful and conversational. Explain your analysis in the 'response_to_user' field.
Produce your response using structured output only.
"""


class SADecision(BaseModel):
    reasoning: str = Field(description="Summary of your internal design decision.")
    response_to_user: str = Field(
        description="A direct, helpful message to the user explaining your analysis and design."
    )
    architecture_note: str = Field(
        description=(
            "A markdown-formatted design note that describes: "
            "1) Which files to create/modify. "
            "2) The structure/API of each file. "
            "3) Any important design constraints."
        )
    )
    affected_files: List[str] = Field(
        description="List of relative file paths that will be created or modified."
    )
    resolved_task_ids: List[str] = Field(
        description="IDs of tasks from the task list that this analysis has resolved."
    )

SADecision.model_rebuild()


def _gather_codebase_context(
    project_root: Path, query: str, max_results: int = 20
) -> str:
    """Search the codebase for snippets relevant to the query."""
    try:
        tool = FileIOTool(project_root)
        results = tool.search_files(query, pattern="**/*.py", case_sensitive=False)
        results += tool.search_files(query, pattern="**/*.md", case_sensitive=False)
        trimmed = results[:max_results]
        if not trimmed:
            return "No relevant code found."
        lines = [
            f"- [{r['file']}:{r['line_number']}] {r['line']}" for r in trimmed
        ]
        return "\n".join(lines)
    except Exception as exc:
        return f"(search failed: {exc})"


def sa_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the System Architect."""
    print("[System Architect] Researching codebase and designing architecture...")

    project_root = Path(config.project_root or ".")
    harness_dir = project_root / ".harness"

    # --- 1. Gather codebase context ----------------------------------------
    keywords = state.user_prompt.split()[:3]
    codebase_context = _gather_codebase_context(project_root, " ".join(keywords))

    # --- 2. Identify which tasks belong to SA --------------------------------
    open_tasks = {
        tid: desc
        for tid, desc in state.tasks.items()
        if tid not in state.completed_tasks
    }

    # --- 3. Call the LLM -----------------------------------------------------
    llm = get_llm(config, "System Architect")
    structured_llm = llm.with_structured_output(SADecision, include_raw=True)

    context_text = (
        f"User Prompt: {state.user_prompt}\n"
        f"Open Tasks (assigned to you): {json.dumps(open_tasks, ensure_ascii=False)}\n"
        f"Already Completed Tasks: {json.dumps(state.completed_tasks, ensure_ascii=False)}\n"
        f"\nCodebase Context (relevant snippets):\n{codebase_context}\n"
    )

    print("[System Architect] Calling LLM for design...")
    
    # Load custom instructions
    custom_instr = PromptManager.load_custom_instructions(harness_dir, "System Architect")
    
    raw_result = structured_llm.invoke(
        [SystemMessage(content=SA_SYSTEM_PROMPT + custom_instr), HumanMessage(content=context_text)]
    )
    
    decision: SADecision = raw_result["parsed"]
    raw_resp = raw_result["raw"]
    
    # Extract token usage
    tokens = extract_token_usage(raw_resp)

    print(f"[System Architect] Design complete. Resolved: {decision.resolved_task_ids}")

    # --- 4. Persist architecture note to .harness/arch_notes.md -------------
    arch_file = harness_dir / "arch_notes.md"
    harness_dir.mkdir(parents=True, exist_ok=True)
    with arch_file.open("a", encoding="utf-8") as f:
        f.write(f"\n\n## Architecture Note\n\n{decision.architecture_note}\n")
        f.write(f"\n**Affected files**: {', '.join(decision.affected_files)}\n")

    # --- 5. Build return payload -------------------------------------------
    new_completed = list(state.completed_tasks) + [
        tid for tid in decision.resolved_task_ids if tid not in state.completed_tasks
    ]

    log = TaskLog(
        agent_name="System Architect",
        action_type="DESIGN",
        input_context=context_text,
        details=decision.response_to_user,
        logs=(
            f"Reasoning: {decision.reasoning}\n"
            f"Affected files: {decision.affected_files}\n"
            f"Codebase context search size: {len(codebase_context)} chars."
        ),
        status="SUCCESS",
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
        "current_assignee": "System Architect",
        "next_agent": "PO",
        "completed_tasks": new_completed,
        "history_logs": [log],
    }
