"""
Tool for agents to read the conversation journal.
Allows agents to extract context from past steps or from other agents' work.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class JournalTool:
    """
    Provides read access to the conversational journal entries.
    """

    def __init__(self, harness_dir: Path) -> None:
        self.harness_dir = harness_dir.resolve()
        self.json_path = self.harness_dir / "conversation.json"

    def read_journal(self, limit: int = 50, role_filter: Optional[str] = None) -> str:
        """
        Reads the most recent `limit` conversational entries.
        If `role_filter` is provided (e.g., 'PO', 'CD'), only returns entries from that role.
        """
        if not self.json_path.exists():
            return "Journal is empty."

        try:
            entries = json.loads(self.json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return "Error reading journal data."

        if role_filter:
            entries = [e for e in entries if e.get("role") == role_filter]

        # Get latest n
        entries = entries[-limit:]

        if not entries:
            return "No entries found."

        # Format output for the agent
        output = []
        for e in entries:
            ts = e.get("timestamp", "")
            r = e.get("role", "Unknown")
            cat = e.get("category", "")
            tgt = e.get("target")
            content = e.get("content", "")
            
            header = f"[{ts}] {r} ({cat}"
            if tgt:
                header += f" -> {tgt}"
            header += ")"
            output.append(f"{header}:\n{content}\n")
            
        return "\n".join(output)
