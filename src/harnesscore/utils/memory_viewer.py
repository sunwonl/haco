from pathlib import Path
import json
from typing import List, Dict, Any
import os

class MemoryViewer:
    """Utility to parse and summarize project memory and session journals."""
    
    @staticmethod
    def get_memory_content(project_root: str) -> Dict[str, Any]:
        """Reads and basic-parses memory.md from the .harness directory."""
        memory_path = Path(project_root) / ".harness" / "memory.md"
        if not memory_path.exists():
            return {"raw": "# No Memory Found\nMemory file does not exist yet.", "sections": []}
        
        content = memory_path.read_text(encoding="utf-8")
        # Simple section parsing by headers
        sections = []
        current_section = None
        for line in content.splitlines():
            if line.startswith("#"):
                if current_section:
                    sections.append(current_section)
                current_section = {"header": line.strip("# "), "content": []}
            elif current_section:
                current_section["content"].append(line)
        
        if current_section:
            sections.append(current_section)
            
        return {
            "raw": content,
            "sections": sections,
            "last_modified": os.path.getmtime(memory_path)
        }

    @staticmethod
    def get_memory_chunks(project_root: str) -> List[Dict[str, Any]]:
        """Parses memory.md and returns a list of chunks for indexing."""
        data = MemoryViewer.get_memory_content(project_root)
        chunks = []
        for sec in data["sections"]:
            header = sec["header"]
            body = "\n".join(sec["content"]).strip()
            if not body: continue
            
            # Combine header and body for better embedding context
            full_text = f"## {header}\n{body}"
            chunks.append({
                "text": full_text,
                "metadata": {"header": header, "source": "memory.md"}
            })
        return chunks

    @staticmethod
    def get_session_timeline(harness_dir: str) -> List[Dict[str, Any]]:
        """Extracts key messages and decisions from journal.jsonl to build a timeline."""
        journal_path = Path(harness_dir) / "journal.jsonl"
        if not journal_path.exists():
            return []
        
        timeline = []
        try:
            with open(journal_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    entry = json.loads(line)
                    # Filter for 'Message' or major 'Decision' points (Action to route/submit)
                    if entry.get("category") == "Message":
                        timeline.append({
                            "timestamp": entry.get("timestamp"),
                            "role": entry.get("role"),
                            "type": "Communication",
                            "content": entry.get("content")
                        })
                    elif entry.get("category") == "Action" and entry.get("target") in ["route_tasks", "submit_work"]:
                        timeline.append({
                            "timestamp": entry.get("timestamp"),
                            "role": entry.get("role"),
                            "type": "Decision",
                            "content": f"Routed task to {entry.get('target')}"
                        })
        except Exception as e:
            print(f"Error parsing journal: {e}")
            
        # Return last 20 events for brevity
        return timeline[-20:]

    @staticmethod
    def format_cli_memory(project_root: str) -> str:
        """Generates a summary of memory for the CLI /memory command."""
        mem = MemoryViewer.get_memory_content(project_root)
        
        output = [
            f"[bold magenta]🧠 PROJECT MEMORY (.harness/memory.md)[/]",
            f"[dim]Last Updated: {time_format(mem.get('last_modified', 0))}[/]",
            ""
        ]
        
        for sec in mem["sections"][:3]: # Show top 3 sections
            output.append(f"[bold cyan]## {sec['header']}[/]")
            text = "\n".join(sec['content']).strip()
            output.append(text[:200] + ("..." if len(text) > 200 else ""))
            output.append("")
            
        output.append("[dim]... (Use Web UI for full visualization)[/]")
        return "\n".join(output)

def time_format(timestamp: float) -> str:
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
