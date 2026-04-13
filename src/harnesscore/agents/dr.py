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
2. **Schema Validation**: Ensure Pydantic/SQLAlchemy models are logically sound and follow best practices.
3. **Consistency Check**: Verify that the proposed changes align with the original user requirement and existing codebase conventions.

### Your Verdict:
- **PASS**: The design is sound, consistent, and ready for the Core Developer to implement.
- **REVISE**: The design has flaws, missing information, or logic errors. Provide specific feedback for the System Architect to fix.

You must be rigorous and technical.
"""

class DRDecision(BaseModel):
    reasoning: str = Field(description="Internal technical analysis of the design.")
    feedback: str = Field(description="Direct message/feedback to the System Architect or User.")
    verdict: Literal["PASS", "REVISE"] = Field(description="Whether to proceed or return for revision.")

DRDecision.model_rebuild()


def dr_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the Design Reviewer."""
    print("[Design Reviewer] Reviewing architecture and schema...")

    project_root = Path(config.project_root or ".")
    harness_dir = project_root / ".harness"
    val_tool = ValidationTool(project_root)
    file_tool = FileIOTool(project_root)

    # --- 1. Gather context ---
    # Read the arch notes created by SA
    arch_notes = ""
    arch_file = harness_dir / "arch_notes.md"
    if arch_file.exists():
        arch_notes = arch_file.read_text(encoding="utf-8")
    else:
        arch_notes = "Error: Architecture notes file missing."

    # Perform automated sync check
    sync_report = val_tool.check_architecture_sync()
    
    # Try to find any newly written schema files to validate
    # (SA often writes docs to docs/ or models.py)
    schema_val_reports = []
    # Heuristic: search for files mentioned in arch_notes and validate if they end in .py
    import re
    files = re.findall(r"#### \[(?:NEW|MODIFY)\]\s+`?([^`\s\(\)]+)`?", arch_notes)
    for f in files:
        if f.endswith(".py"):
            schema_val_reports.append(val_tool.validate_schema(f))

    # --- 2. Call LLM ---
    llm = get_llm(config, "Design Reviewer")
    structured_llm = llm.with_structured_output(DRDecision)

    context_lines = [
        f"User Prompt: {state.user_prompt}",
        f"\n--- Architecture Notes ---\n{arch_notes}",
        f"\n--- Automated Sync Report ---\n{sync_report}",
        f"\n--- Schema Validation Reports ---\n" + ("\n".join(schema_val_reports) if schema_val_reports else "No schema files to validate."),
    ]

    print("[Design Reviewer] Calling LLM for design verdict...")
    
    # Load custom instructions
    custom_instr = PromptManager.load_custom_instructions(harness_dir, "Design Reviewer")
    
    decision: DRDecision = structured_llm.invoke([
        SystemMessage(content=DR_SYSTEM_PROMPT + custom_instr),
        HumanMessage(content="\n".join(context_lines))
    ])
    
    print(f"[Design Reviewer] Verdict: {decision.verdict}")

    # --- 3. Build return payload ---
    log = TaskLog(
        agent_name="Design Reviewer",
        action_type="REVIEW",
        details=decision.feedback,
        logs=(
            f"Verdict: {decision.verdict}\n"
            f"Reasoning: {decision.reasoning}\n"
            f"Sync Report: {sync_report}"
        ),
        status="SUCCESS" if decision.verdict == "PASS" else "FAIL"
    )

    Journaler.log_activity(
        harness_dir=harness_dir,
        thread_id=getattr(state, "thread_id", "unknown"),
        log_data=log.model_dump(),
        language=config.language
    )

    return {
        "current_assignee": "Design Reviewer",
        "next_agent": "Core Developer" if decision.verdict == "PASS" else "System Architect",
        "latest_error": decision.feedback if decision.verdict == "REVISE" else None,
        "history_logs": [log],
    }
