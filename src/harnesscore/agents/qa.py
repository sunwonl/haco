"""
QA Evaluator agent node.
"""
import json
from pathlib import Path
from typing import Literal, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from harnesscore.schema import SystemState, TaskLog
from harnesscore.config.loader import HarnessConfig
from harnesscore.llm import get_llm
from harnesscore.utils.journaler import Journaler
from harnesscore.utils.prompt_manager import PromptManager
from harnesscore.tools.file_io import FileIOTool
from harnesscore.tools.network import NetworkTool
from harnesscore.tools.shell import ShellTool
from harnesscore.tools.process_control import ProcessControlTool


QA_SYSTEM_PROMPT = """\
You are the **QA Evaluator** of an autonomous software engineering team.

Your responsibilities:
1. **Implementation Review**: Review code changes and cross-check with requirements.
2. **Runtime Verification**: Use your Network and Shell tools to verify if the implementation actually works.
   - You can ping endpoints to check server status.
   - You can run test suites (pytest, etc.) via ShellTool.
3. **Decide Status**: 
   - Set `status` to "APPROVED" if the goal is met and verified.
   - Set `status` to "REJECTED" if there are errors, bugs, or missing functionality.

If REJECTED, specify exactly what is missing or failed in `feedback`.
"""


class QADecision(BaseModel):
    reasoning: str = Field(description="Internal technical reasoning for your evaluation.")
    response_to_user: str = Field(
        description="A direct message to the user explaining your verification results."
    )
    status: Literal["APPROVED", "REJECTED"] = Field(
        description="Whether the current state satisfies the requirements."
    )
    feedback: str = Field(
        description="Technical feedback for agents if REJECTED. Empty if APPROVED."
    )

QADecision.model_rebuild()


def qa_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the QA Evaluator."""
    print("[QA Evaluator] Performing deep verification...")

    project_root = Path(config.project_root or ".")
    file_tool = FileIOTool(project_root)
    net_tool = NetworkTool()
    shell_tool = ShellTool(project_root)
    proc_tool = ProcessControlTool(project_root)

    # --- 1. Automatic Diagnostics ------------------------------------------
    # Check if there are any running servers from ProcessControl
    running_procs = proc_tool.status()
    proc_summary = "\n".join([f"- {p['label']}: {p['status']} (PID {p['pid']})" for p in running_procs]) or "No background processes."

    # Perform a quick health check if it's a web project (looking for local ports)
    # This is a bit heuristic, but useful for QA
    health_results = []
    if any("fastapi" in str(state.file_changes).lower() for p in state.file_changes):
        # Heuristic: try localhost:8000 for FastAPI
        health_results.append(net_tool.ping("http://localhost:8000/health"))

    # Read the modified files
    file_contents = {}
    for path in state.file_changes:
        try:
            content = file_tool.view_file(path)
            file_contents[path] = content
        except:
            pass

    # --- 2. Call LLM -------------------------------------------------------
    llm = get_llm(config, "QA Evaluator")
    structured_llm = llm.with_structured_output(QADecision)

    context_text = (
        f"User Prompt: {state.user_prompt}\n"
        f"Modified Files: {state.file_changes}\n"
        f"Latest Error: {state.latest_error or 'None'}\n"
        f"Background Processes:\n{proc_summary}\n"
        f"Automatic Health Checks:\n" + ("\n".join(health_results) if health_results else "None run.") + "\n"
        f"\n--- File Contents ---\n"
        f"{json.dumps(file_contents, indent=2, ensure_ascii=False)}\n"
    )

    print("[QA Evaluator] Calling LLM for final verdict...")
    
    # Load custom instructions
    harness_dir = project_root / ".harness"
    custom_instr = PromptManager.load_custom_instructions(harness_dir, "QA Evaluator")
    
    decision: QADecision = structured_llm.invoke(
        [SystemMessage(content=QA_SYSTEM_PROMPT + custom_instr), HumanMessage(content=context_text)]
    )
    
    print(f"[QA Evaluator] Verdict: {decision.status}")

    # --- 3. Build return payload ------------------------------------------
    log = TaskLog(
        agent_name="QA Evaluator",
        action_type="VERIFICATION",
        details=decision.response_to_user,
        logs=(
            f"Status: {decision.status}\n"
            f"Feedback: {decision.feedback}\n"
            f"Reasoning: {decision.reasoning}\n"
            f"Procs: {proc_summary}\n"
            f"Health: {health_results}"
        ),
        status="SUCCESS" if decision.status == "APPROVED" else "FAIL"
    )

    harness_dir = project_root / ".harness"
    Journaler.log_activity(
        harness_dir=harness_dir,
        thread_id=getattr(state, "thread_id", "unknown"),
        log_data=log.model_dump(),
        language=config.language
    )

    return {
        "current_assignee": "QA Evaluator",
        "next_agent": "PO",
        "latest_error": decision.feedback if decision.status == "REJECTED" else None,
        "history_logs": [log],
    }
