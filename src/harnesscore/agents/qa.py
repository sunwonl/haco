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


from harnesscore.agents.base import run_agent_react_loop
from harnesscore.tools.journal import JournalTool

def qa_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the QA Evaluator."""
    project_root = Path(config.project_root or ".")
    harness_dir = project_root / ".harness"
    llm = get_llm(config, "QA Evaluator")

    sys_prompt = QA_SYSTEM_PROMPT + PromptManager.load_custom_instructions(harness_dir, "QA Evaluator")

    # Define dynamic tools for QA
    def system_status() -> str:
        """Get the current running background processes (e.g., servers)."""
        proc_tool = ProcessControlTool(project_root)
        running_procs = proc_tool.status()
        return "\n".join([f"- {p['label']}: {p['status']} (PID {p['pid']})" for p in running_procs]) or "No background processes."

    def network_ping(url: str) -> str:
        """Ping a URL (e.g. http://localhost:8000/health) to check if server is responding."""
        net_tool = NetworkTool()
        return net_tool.ping(url)
        
    def read_file(path: str) -> str:
        """Read content of a specific file."""
        file_tool = FileIOTool(project_root)
        try:
            return file_tool.view_file(path)
        except Exception as e:
            return f"Error: {e}"

    def run_tests(command: str) -> str:
        """Run a test command synchronously (e.g. 'pytest')."""
        shell_tool = ShellTool(project_root)
        return shell_tool.run_command(command)

    def read_journal(target_role: str = "PO", limit: int = 5) -> str:
        """Read what other agents discussed."""
        jtool = JournalTool(harness_dir)
        return jtool.read_journal(limit=limit, role_filter=target_role)

    def submit_work(status: Literal["APPROVED", "REJECTED"], message: str, next_agent: str = "PO", completed_task_id: str = None) -> str:
        """
        Submit your QA evaluation result.
        Args:
            status: "APPROVED" if requirements are fully met without errors, else "REJECTED".
            message: Explanation or feedback.
            next_agent: Always route back to "PO".
            completed_task_id: The ID of the task you evaluated, if any.
        """
        return "WORK_SUBMITTED"

    def run_shell_command(command: str) -> str:
        """Run robust linux shell commands (e.g., cat, grep, ls, python) to inspect the codebase or execute scripts."""
        shell_tool = ShellTool(project_root)
        return shell_tool.run_command(command)

    tools = [system_status, network_ping, read_file, run_tests, read_journal, submit_work, run_shell_command]

    context_str = (
        f"User Prompt: {state.user_prompt}\n"
        f"Tasks Queue: {json.dumps(state.tasks, ensure_ascii=False)}\n"
        f"Modified Files to evaluate: {state.file_changes}\n"
        f"Latest Error Context: {state.latest_error or 'None'}\n"
    )

    result = run_agent_react_loop(
        agent_name="QA Evaluator",
        state=state,
        llm=llm,
        tools=tools,
        sys_prompt=sys_prompt,
        context_str=context_str,
        harness_dir=harness_dir,
        max_loops=10
    )
    
    # QA handles 'latest_error' uniquely inside result state
    # We need to extract the status from the tool calls, but since it's hard to parse post-loop robustly without looking into JournalEntry,
    # let's just use the message content if we rejected.
    # A quick heuristic: if the message starts with or contains 'REJECT', set latest_error
    last_msg = ""
    for j in result["journal"]:
        if j.category == "Message":
            last_msg = j.content.upper()
    if "REJECT" in last_msg or "FAIL" in last_msg:
        result["latest_error"] = last_msg

    return result
