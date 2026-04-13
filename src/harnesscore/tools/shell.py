"""
Safe shell command execution tool for agents.
Provides synchronous execution of bash commands with safety guards.
"""
import subprocess
import os
from pathlib import Path
from typing import List, Optional, Tuple


class ShellTool:
    """
    Executes shell commands within the project root.
    Includes basic safety checks (Path Guard, Disallowed commands).
    """

    # Commands that are explicitly forbidden for security reasons
    FORBIDDEN_COMMANDS = {
        "rm -rf /", "mkfs", "dd", "shutdown", "reboot", "nmap", "ssh"
    }

    def __init__(self, project_root: Path, timeout: int = 60):
        self.project_root = project_root.resolve()
        self.timeout = timeout

    def run_command(self, command: str, cwd: Optional[str] = None) -> str:
        """
        Run a bash command synchronously.
        
        Args:
            command: The full command string to execute.
            cwd: Optional relative path from project root to run the command in.
            
        Returns:
            Combined stdout and stderr.
        """
        # 1. Basic security check
        if any(forbidden in command for forbidden in self.FORBIDDEN_COMMANDS):
            return f"Error: Command contains forbidden patterns."

        # 2. Resolve CWD safely
        exec_cwd = self.project_root
        if cwd:
            target_cwd = (self.project_root / cwd).resolve()
            if not str(target_cwd).startswith(str(self.project_root)):
                return f"Error: CWD '{cwd}' is outside project root."
            exec_cwd = target_cwd

        # 3. Execute
        try:
            print(f"[ShellTool] Executing: {command} (cwd: {exec_cwd.relative_to(self.project_root)})")
            result = subprocess.run(
                command,
                shell=True,
                cwd=exec_cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={**os.environ, "PAGER": "cat"} # Force non-interactive pager
            )
            
            output = result.stdout + result.stderr
            status = "Success" if result.returncode == 0 else f"Failed (Internal Return Code: {result.returncode})"
            
            return f"--- Command Output ({status}) ---\n{output}"
            
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {self.timeout} seconds."
        except Exception as e:
            return f"Error: Unexpected failure during execution: {str(e)}"

    def list_files_tree(self, depth: int = 2) -> str:
        """Helper to show directory structure (useful for PO/SA)."""
        return self.run_command(f"find . -maxdepth {depth} -not -path '*/.*'")
