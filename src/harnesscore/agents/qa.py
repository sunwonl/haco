"""
QA Evaluator agent node.

Responsibilities:
- Verify the final implementation against the user requirement.
- Check test results and codebase state.
- Surface any lingering issues or bugs back to PO.
- If everything is perfect, signal FINISH.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from harnesscore.schema import SystemState, TaskLog
from harnesscore.config.loader import HarnessConfig
from harnesscore.llm import get_llm
from harnesscore.tools.file_io import FileIOTool


QA_SYSTEM_PROMPT = """\
You are the **QA Evaluator** of an autonomous software engineering team.

Your responsibilities:
1. Review the files modified by the Core Developer.
2. Cross-check the implementation with the original user requirement.
3. Analyze the latest error (if any) and test outputs provided in the history.
4. Decide if the project is ready to be delivered or if it needs more work.

If you find an issue (bug, missing feature, failed test), describe it clearly in `feedback`.
If everything is correct and ready, set `status` to "APPROVED".

Produce your response using structured output only.
"""


class QADecision(BaseModel):
    reasoning: str = Field(description="Internal reasoning for your evaluation.")
    status: Literal["APPROVED", "REJECTED"] = Field(
        description="Whether the current state satisfies the requirements."
    )
    feedback: str = Field(
        description="Detailed feedback if REJECTED. Empty if APPROVED."
    )


def qa_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the QA Evaluator."""
    print("[QA Evaluator] Performing final verification...")

    project_root = Path(config.project_root or ".")
    file_tool = FileIOTool(project_root)

    # --- 1. Gather context ------------------------------------------------
    # Read the modified files to verify content
    file_contents = {}
    for path in state.file_changes:
        try:
            content = file_tool.view_file(path)
            file_contents[path] = content
        except:
            file_contents[path] = f"(Error reading file {path})"

    # Get the implementation logs from history
    impl_logs = [
        log for log in state.history_logs if log.agent_name == "Core Developer"
    ]
    latest_impl_detail = impl_logs[-1].details if impl_logs else "No implementation logs found."

    # --- 2. Call LLM -------------------------------------------------------
    llm = get_llm(config, "QA Evaluator")
    structured_llm = llm.with_structured_output(QADecision)

    context_text = (
        f"User Prompt: {state.user_prompt}\n"
        f"Modified Files: {state.file_changes}\n"
        f"Test/Impl Results: {latest_impl_detail}\n"
        f"Latest Error: {state.latest_error or 'None'}\n"
        f"\n--- Current File Contents ---\n"
        f"{json.dumps(file_contents, indent=2, ensure_ascii=False)}\n"
    )

    decision: QADecision = structured_llm.invoke(
        [SystemMessage(content=QA_SYSTEM_PROMPT), HumanMessage(content=context_text)]
    )

    print(f"[QA Evaluator] Result: {decision.status}")
    if decision.status == "REJECTED":
        print(f"[QA Evaluator] Feedback: {decision.feedback}")

    # --- 3. Build return payload ------------------------------------------
    log = TaskLog(
        agent_name="QA Evaluator",
        action_type="VERIFICATION",
        details=f"Status: {decision.status}. Feedback: {decision.feedback}",
        status="SUCCESS" if decision.status == "APPROVED" else "FAIL",
    )

    return {
        "current_assignee": "QA Evaluator",
        "next_agent": "PO", # Always go back to PO to let them decide FINISH or correction
        "latest_error": decision.feedback if decision.status == "REJECTED" else None,
        "history_logs": [log],
    }
