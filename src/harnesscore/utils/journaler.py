"""
Utility for explicit activity journaling in HarnessCore.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import threading

class Journaler:
    _lock = threading.Lock()
    
    @staticmethod
    def append_entry(harness_dir: Path, dict_entry: dict) -> None:
        """
        Appends a conversational JournalEntry to timeline.md and conversation.json.
        dict_entry is the dump of JournalEntry to avoid circular imports.
        """
        import json
        timeline_path = harness_dir / "timeline.md"
        json_path = harness_dir / "conversation.json"
        
        ts = dict_entry.get("timestamp", "")
        session_id = dict_entry.get("session_id", "")
        role = dict_entry.get("role", "Unknown")
        category = dict_entry.get("category", "")
        target = dict_entry.get("target")
        content = dict_entry.get("content", "")
        tokens = dict_entry.get("tokens", {})
        
        cat_str = category
        if category == "Message" and target:
            cat_str = f"메시지: to {target}"
        elif category == "Action" and target:
            cat_str = f"Action : use tool> {target}" # matches requested format kind of
        elif category == "Result":
            cat_str = "Action : result"
        
        md_line = f"- [{role}] : <{cat_str}> {content}"
        
        in_t = tokens.get("input_tokens", 0)
        out_t = tokens.get("output_tokens", 0)
        think_t = tokens.get("thinking_tokens", 0)
        tokens_line = f"- Tokens: `in: {in_t}` | `out: {out_t}` | `think: {think_t}`"
        
        entry_md = f"## [{ts}] : {session_id}\n{md_line}\n{tokens_line}\n\n"
        
        with Journaler._lock:
            if not timeline_path.exists():
                timeline_path.write_text("# HarnessCore Timeline\n\n", encoding="utf-8")
            with timeline_path.open("a", encoding="utf-8") as f:
                f.write(entry_md)
                
            # Append to JSON
            existing = []
            if json_path.exists():
                try:
                    existing = json.loads(json_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass
            existing.append(dict_entry)
            json_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")

    
    @staticmethod
    def log_activity(harness_dir: Path, thread_id: str, log_data: dict, language: str = "en") -> None:
        """
        Writes a detailed, human-readable log entry to journals.md.
        """
        journal_path = harness_dir / "journals.md"
        ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Localization Map
        i18n = {
            "en": {
                "status": "Status",
                "summary": "Summary",
                "reasoning": "Reasoning",
                "affected_files": "Affected Files",
                "tokens": "Tokens",
                "session": "Session",
                "action": "Action"
            },
            "ko": {
                "status": "상태",
                "summary": "요약",
                "reasoning": "추론",
                "affected_files": "변경 파일",
                "tokens": "토큰 사용량",
                "session": "세션",
                "action": "작업"
            }
        }
        
        # Fallback to English if language not supported
        lang_map = i18n.get(language, i18n["en"])

        icons = {
            "PO": "👨‍✈️",
            "System Architect": "🏗️",
            "Core Developer": "💻",
            "UI Engineer": "🎨",
            "QA Evaluator": "🧪",
            "Design Reviewer": "🔍",
            "System Orchestrator": "🤖"
        }
        
        agent = log_data.get("agent_name", "unknown")
        icon = icons.get(agent, "🤖")
        status_icon = "✅" if log_data.get("status") == "SUCCESS" else "❌"
        
        # Build Entry
        lines = [
            f"\n## [{ts}] {lang_map['session']}: `{thread_id[:8]}`",
            f"### {icon} **{agent}** | {lang_map['action']}: `{log_data.get('action_type')}`",
            f"- **{lang_map['status']}**: {status_icon} `{log_data.get('status')}`",
            f"- **{lang_map['summary']}**: {log_data.get('details')}"
        ]
        
        if log_data.get("reasoning"):
            lines.append(f"- **{lang_map['reasoning']}**: {log_data.get('reasoning')}")
            
        if log_data.get("affected_files"):
            files = ", ".join([f"`{f}`" for f in log_data.get("affected_files")])
            lines.append(f"- **{lang_map['affected_files']}**: {files}")
            
        tokens = log_data.get("tokens")
        if tokens:
            it = tokens.get("input_tokens", 0)
            ot = tokens.get("output_tokens", 0)
            tt = tokens.get("thinking_tokens", 0)
            lines.append(f"- **{lang_map['tokens']}**: 🪙 `in: {it}` | `out: {ot}` | `think: {tt}`")
            
        lines.append("-----")
        entry = "\n".join(lines) + "\n"
        
        with Journaler._lock:
            if not journal_path.exists():
                title = "HarnessCore Activity Journal" if language == "en" else "HarnessCore 활동 기록"
                journal_path.write_text(f"# {title}\n")
            with journal_path.open("a") as f:
                f.write(entry)
