"""
Git operations tool for agents.
Wraps subprocess git commands with safety constraints.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    """Raised when a git command exits with a non-zero code."""


class GitTool:
    """
    Safe git operations confined to *repo_root*.

    Only a curated allow-list of git sub-commands can be executed.
    """

    ALLOWED_SUBCOMMANDS: frozenset[str] = frozenset(
        {
            "status",
            "log",
            "diff",
            "branch",
            "checkout",
            "add",
            "commit",
            "reset",
            "stash",
        }
    )

    def __init__(self, repo_root: Path, timeout: int = 30) -> None:
        self.repo_root = repo_root.resolve()
        self.timeout = timeout

    # ------------------------------------------------------------------ #
    #  Internal runner                                                     #
    # ------------------------------------------------------------------ #
    def _run(self, args: list[str]) -> str:
        """Execute a git command and return stdout. Raise GitError on failure."""
        subcommand = args[0] if args else ""
        if subcommand not in self.ALLOWED_SUBCOMMANDS:
            raise PermissionError(
                f"git '{subcommand}' is not in the allowed list: {sorted(self.ALLOWED_SUBCOMMANDS)}"
            )
        cmd = ["git", *args]
        result = subprocess.run(
            cmd,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        if result.returncode != 0:
            raise GitError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #
    def status(self) -> str:
        """Return `git status --short` output."""
        return self._run(["status", "--short"])

    def log(self, n: int = 10) -> str:
        """Return last *n* commit hashes + messages (one-line format)."""
        return self._run(["log", f"-{n}", "--oneline"])

    def diff(self, path: str = "") -> str:
        """Return `git diff` for a specific file or all staged/unstaged files."""
        args = ["diff"]
        if path:
            args.append(path)
        return self._run(args)

    def create_branch(self, branch_name: str, base: str = "HEAD") -> str:
        """Create and switch to a new branch from *base*."""
        return self._run(["checkout", "-b", branch_name, base])

    def checkout(self, ref: str) -> str:
        """Switch to an existing branch or commit ref."""
        return self._run(["checkout", ref])

    def add(self, path: str = ".") -> str:
        """Stage files for commit."""
        return self._run(["add", path])

    def commit(self, message: str) -> str:
        """Create a commit with *message*. Stages are assumed to be set."""
        return self._run(["commit", "-m", message])

    def rollback(self, mode: str = "--hard") -> str:
        """
        Roll back to HEAD.

        *mode* must be one of '--hard', '--soft', '--mixed'.
        Defaults to '--hard' (destructive: discards working tree changes).
        """
        if mode not in {"--hard", "--soft", "--mixed"}:
            raise ValueError(f"Invalid reset mode: {mode}")
        return self._run(["reset", mode, "HEAD"])

    def stash(self) -> str:
        """Stash current working-tree changes."""
        return self._run(["stash"])

    def list_branches(self) -> list[str]:
        """Return all local branch names."""
        raw = self._run(["branch", "--format=%(refname:short)"])
        return [b.strip() for b in raw.splitlines() if b.strip()]
