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
Your goal is to transform high-level requirements into a robust, scalable, and maintainable technical blueprint.

### Your Responsibilities:
1. **System Architecture Design**: Define the overall file structure, directory layout, and integration points with external systems or databases.
2. **Software Module Design**: Design specific classes, functions, and data structures. Ensure high cohesion and loose coupling.
3. **Spec for CD**: Define files, classes, and API signatures so clearly that the Core Developer (CD) can implement them without further clarification.
4. **Technical Blueprint**: Produce comprehensive architecture notes in `.harness/arch_notes.md` or `docs/SYSTEM_ARCHITECTURE.md`.

### Your Design Principles:
- **Clean Architecture & SOLID**: Apply industry-standard design principles to ensure the code is testable and extensible.
- **Interface-First**: Define abstract interfaces or base classes before jumping into implementation details.
- **Visual Documentation**: Use **Mermaid diagrams** (sequence, class, or flowcharts) within your design notes to visualize complex logic or component interactions.
- **Traceability**: Clearly map your design decisions back to the tasks assigned by the PO.

### Guidelines:
- Analyze the existing codebase (`codebase_context`) thoroughly before proposing changes to ensure consistency.
- Explain your technical reasoning clearly in the 'response_to_user' field so the user understands the "Why" behind your architecture.
- Mark resolved tasks as completed in the 'resolved_task_ids' field.

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


from harnesscore.agents.base import run_agent_react_loop
from harnesscore.tools.journal import JournalTool

async def sa_node(state: SystemState, config: HarnessConfig) -> dict:
    """LangGraph node execution for the System Architect."""
    project_root = Path(config.project_root or ".")
    harness_dir = project_root / ".harness"
    llm = get_llm(config, "System Architect")
    
    sys_prompt = SA_SYSTEM_PROMPT + PromptManager.load_custom_instructions(harness_dir, "System Architect")
    
    def search_codebase(query: str, pattern: str = "**/*.py") -> str:
        """Search the codebase for snippets relevant to the query to identify files needing changes."""
        tool = FileIOTool(project_root)
        try:
            results = tool.search_files(query, pattern=pattern)
            lines = [f"[{r['file']}:{r['line_number']}] {r['line']}" for r in results[:20]]
            return "\n".join(lines) if lines else "No relevant code found."
        except Exception as e:
            return f"Error: {e}"
            
    def write_architecture_note(content: str, affected_files: str) -> str:
        """Write the architecture note to guide Core Developer."""
        arch_file = harness_dir / "arch_notes.md"
        harness_dir.mkdir(parents=True, exist_ok=True)
        with arch_file.open("a", encoding="utf-8") as f:
            f.write(f"\n\n## Architecture Note\n\n{content}\n")
            f.write(f"\n**Affected files**: {affected_files}\n")
        return "Note written successfully. arch_notes.md updated."

    def read_journal(target_role: str = "PO", limit: int = 5) -> str:
        """Read what other agents discussed."""
        jtool = JournalTool(harness_dir)
        return jtool.read_journal(limit=limit, role_filter=target_role)

    def submit_work(message: str, next_agent: str = "PO", completed_task_id: str = None) -> str:
        """Submit the architecture spec for review or implementation."""
        return "WORK_SUBMITTED"

    def run_shell_command(command: str) -> str:
        """Run robust linux shell commands (e.g., cat, grep, ls, python) to inspect the codebase or execute scripts."""
        from harnesscore.tools.shell import ShellTool
        shell_tool = ShellTool(project_root)
        return shell_tool.run_command(command)

    tools = [search_codebase, write_architecture_note, read_journal, submit_work, run_shell_command]
    
    open_tasks = {
        tid: desc for tid, desc in state.tasks.items() if tid not in state.completed_tasks
    }
    context_str = (
        f"User Prompt: {state.user_prompt}\n"
        f"Open Tasks (assigned to you): {json.dumps(open_tasks, ensure_ascii=False)}\n"
        f"Already Completed Tasks: {json.dumps(state.completed_tasks, ensure_ascii=False)}\n"
    )

    return await run_agent_react_loop(
        agent_name="System Architect", state=state, llm=llm, tools=tools, 
        sys_prompt=sys_prompt, context_str=context_str, harness_dir=harness_dir, max_loops=10
    )
