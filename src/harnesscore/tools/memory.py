"""
Global Semantic Memory Tool.
Provides long-term knowledge retention for agents across different sessions.
"""
from pathlib import Path
from datetime import datetime, timezone

class MemoryTool:
    """
    Manages long-term semantic memory stored in .harness/memory.md.
    """
    def __init__(self, harness_dir: Path):
        self.harness_dir = harness_dir
        self.memory_file = harness_dir / "memory.md"
        
    def add_memory(self, fact: str) -> str:
        """
        Save a specific user preference, structural rule, or important context to global memory.
        
        Args:
            fact: The statement or rule to remember (e.g., "User prefers TypeScript over JavaScript.")
        """
        self.harness_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        content = f"- [{timestamp}] {fact}\n"
        with self.memory_file.open("a", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully recorded into global memory: '{fact}'"
        
    def read_memory(self) -> str:
        """
        Read all currently stored global memory facts.
        """
        if not self.memory_file.exists():
            return "No global memory items stored yet."
        return self.memory_file.read_text(encoding="utf-8")
