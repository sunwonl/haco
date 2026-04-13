"""
Validation and consistency checking tools for agents.
Helps Design Reviewers verify schema correctness and architecture alignment.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from harnesscore.tools.shell import ShellTool


class ValidationTool:
    """
    Provides methods to validate the integrity of the project's design and code.
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.shell = ShellTool(self.project_root)

    def validate_schema(self, file_path: str) -> str:
        """
        Run a static check (using ruff/pyright) on a schema/model file.
        
        Args:
            file_path: Path to the python file containing models.
            
        Returns:
            Success or a list of static analysis errors.
        """
        # We try to use ruff if available as it's fast
        cmd = f"ruff check {file_path} --select E,F,W"
        result = self.shell.run_command(cmd)
        
        if "Success" in result:
            return f"VALIDATION SUCCESS: {file_path} passed basic static checks."
        else:
            return f"VALIDATION FAIL: Issues found in {file_path}:\n{result}"

    def check_architecture_sync(self, arch_doc_path: str = ".harness/arch_notes.md") -> str:
        """
        Check if the files listed in the architecture notes actually exist and are populated.
        
        Returns:
            A summary of missing or empty files compared to the design.
        """
        target = self.project_root / arch_doc_path
        if not target.exists():
            return "Error: Architecture documentation not found."

        content = target.read_text(encoding="utf-8")
        
        # Heuristic: find lines starting with #### [NEW] or #### [MODIFY]
        discrepancies = []
        import re
        files_in_doc = re.findall(r"#### \[(?:NEW|MODIFY)\]\s+`?([^`\s\(\)]+)`?", content)
        
        if not files_in_doc:
            return "No specific files identified in the architecture document using standard markers."

        for rel_path in files_in_doc:
            file_path = self.project_root / rel_path.lstrip("/")
            if not file_path.exists():
                discrepancies.append(f"MISSING: {rel_path} (Defined in arch doc but not on disk)")
            elif file_path.stat().st_size == 0:
                discrepancies.append(f"EMPTY: {rel_path} (Exists but has 0 bytes)")

        if not discrepancies:
            return "SYNC SUCCESS: All files defined in architecture documentation exist and are non-empty."
        else:
            return "SYNC DISCREPANCY:\n" + "\n".join(discrepancies)

    def compare_requirements(self, user_prompt: str, current_state_summary: str) -> str:
        """
        Helper for the agent to compare requirements against current state.
        This is mostly a wrapper to structured input for the agent, but
        could include more logic later (e.g. checking log persistence).
        """
        # Placeholder for more complex logic
        return f"Requirements: {user_prompt}\nState: {current_state_summary}"
