"""
File I/O tool for agents.
Provides safe, sandboxed file-read and file-write operations
restricted to the declared project root (Path Guard).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


class PathGuardError(PermissionError):
    """Raised when an agent tries to access a path outside the project root."""


class FileIOTool:
    """
    Safe file I/O operations constrained to *project_root*.

    All path arguments are resolved to absolute paths and checked against
    *project_root* before any I/O takes place.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    # ------------------------------------------------------------------ #
    #  Internal guard                                                      #
    # ------------------------------------------------------------------ #
    def _safe_path(self, path: str | Path) -> Path:
        resolved = (self.project_root / path).resolve()
        if not str(resolved).startswith(str(self.project_root)):
            raise PathGuardError(
                f"Access denied: '{resolved}' is outside project root '{self.project_root}'"
            )
        return resolved

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #
    def view_file(self, path: str, start_line: int = 1, end_line: Optional[int] = None) -> str:
        """
        Read a file (or a line range) and return its content as a string.
        Lines are 1-indexed.
        """
        target = self._safe_path(path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {target}")

        lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
        # Clamp to valid range
        start = max(1, start_line) - 1
        end = (end_line or len(lines))
        return "".join(lines[start:end])

    def write_file(self, path: str, content: str) -> str:
        """Create or overwrite a file with *content*."""
        target = self._safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Written: {target}"

    def append_file(self, path: str, content: str) -> str:
        """Append *content* to a file (creates it if missing)."""
        target = self._safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as f:
            f.write(content)
        return f"Appended to: {target}"

    def replace_content(self, path: str, target_str: str, replacement: str) -> str:
        """
        Replace the *first* occurrence of *target_str* in the file with *replacement*.
        Raises ValueError if *target_str* is not found.
        """
        fpath = self._safe_path(path)
        original = fpath.read_text(encoding="utf-8")
        if target_str not in original:
            raise ValueError(f"Target string not found in '{fpath}'")
        updated = original.replace(target_str, replacement, 1)
        fpath.write_text(updated, encoding="utf-8")
        return f"Replaced in: {fpath}"

    def search_files(
        self,
        query: str,
        pattern: str = "**/*",
        case_sensitive: bool = False,
    ) -> list[dict]:
        """
        Grep-style search across files matching *pattern*.
        Returns a list of {file, line_number, line} dicts.
        """
        results: list[dict] = []
        for fpath in self.project_root.glob(pattern):
            if not fpath.is_file():
                continue
            try:
                for i, line in enumerate(
                    fpath.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1
                ):
                    needle = query if case_sensitive else query.lower()
                    haystack = line if case_sensitive else line.lower()
                    if needle in haystack:
                        results.append(
                            {
                                "file": str(fpath.relative_to(self.project_root)),
                                "line_number": i,
                                "line": line.strip(),
                            }
                        )
            except (OSError, UnicodeDecodeError):
                continue
        return results

    def list_directory(self, path: str = ".") -> list[str]:
        """List files and subdirectories under *path*."""
        target = self._safe_path(path)
        if not target.is_dir():
            raise NotADirectoryError(f"Not a directory: {target}")
        return sorted(
            str(p.relative_to(self.project_root))
            for p in target.iterdir()
        )
