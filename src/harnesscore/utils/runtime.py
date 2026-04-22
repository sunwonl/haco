import psutil
import os
import time
from typing import Dict, Any
from ..schema import SystemState, TokenUsage

class RuntimeProfiler:
    """Utility to collect runtime statistics for both CLI and Web interfaces."""
    
    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """Returns CPU and Memory usage of the current process."""
        process = psutil.Process(os.getpid())
        with process.oneshot():
            cpu_percent = process.cpu_percent(interval=None)
            mem_info = process.memory_info()
            mem_rss_mb = mem_info.rss / (1024 * 1024)
            
        return {
            "cpu_percent": cpu_percent,
            "memory_mb": round(mem_rss_mb, 2),
            "pid": os.getpid(),
            "uptime_sec": round(time.time() - psutil.boot_time(), 0) # This is system uptime, maybe process start time is better
        }

    @staticmethod
    def get_token_summary(state: SystemState) -> Dict[str, Any]:
        """Calculates costs and returns a formatted summary of token usage."""
        usage = state.total_tokens
        # Simple cost estimation (e.g., $15/1M input, $60/1M output for Pro-type models)
        input_cost = (usage.input_tokens / 1_000_000) * 15.0
        output_cost = (usage.output_tokens / 1_000_000) * 60.0
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "thinking_tokens": usage.thinking_tokens,
            "total_tokens": usage.input_tokens + usage.output_tokens,
            "estimated_cost_usd": round(total_cost, 4)
        }

    @staticmethod
    def format_cli_report(state: SystemState) -> str:
        """Generates a rich-compatible string for the CLI /runtime command."""
        sys = RuntimeProfiler.get_system_stats()
        tok = RuntimeProfiler.get_token_summary(state)
        
        report = [
            "[bold cyan]🚀 HARNESS_CORE RUNTIME REPORT[/]",
            f"• [bold]PID:[/] {sys['pid']}",
            f"• [bold]CPU Usage:[/] {sys['cpu_percent']}%",
            f"• [bold]Memory RSS:[/] {sys['memory_mb']} MB",
            "",
            "[bold green]💰 TOKEN CONSUMPTION[/]",
            f"• [bold]Input:[/] {tok['input_tokens']:,}",
            f"• [bold]Output:[/] {tok['output_tokens']:,}",
            f"• [bold]Thinking:[/] {tok['thinking_tokens']:,}",
            f"• [bold]Total Cost:[/] ${tok['estimated_cost_usd']:.4f}",
            "",
            "[bold yellow]📂 PROJECT STATUS[/]",
            f"• [bold]Tasks Completed:[/] {len(state.completed_tasks)} / {len(state.tasks)}"
        ]
        return "\n".join(report)
