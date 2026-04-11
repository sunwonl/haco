"""
HarnessCore CLI entry point.

Usage:
  harness cli     - Launch TUI mode (Textual app)
  harness web     - Launch Web dashboard mode (FastAPI + browser)
  harness init    - Initialize .harness/ config in current directory
"""
from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

from harnesscore.config.loader import load_config

load_dotenv()

app = typer.Typer(
    name="harness",
    help="HarnessCore AI - Self-iterative multi-agent coding engine",
    add_completion=False,
)
console = Console()


@app.command()
def init() -> None:
    """Initialize .harness/ configuration in the current directory."""
    config = load_config()

    console.print(
        "[bold green]✓[/] Initialized [bold].harness/settings.json[/]\n"
        f"  Provider : [cyan]{config.llm.provider}[/]\n"
        f"  Model    : [cyan]{config.llm.default_model}[/]"
    )

    # Credential check
    api_key = config.resolve_api_key()
    if api_key:
        console.print(f"  Auth     : [green]✓[/] {config.credentials.api_key_env} is set")
    else:
        console.print(
            f"\n[bold yellow]⚠[/]  API key not found.\n"
            f"  Set the [bold]{config.credentials.api_key_env}[/] environment variable before running agents.\n"
            f"  Example: [dim]export {config.credentials.api_key_env}=your-api-key[/]"
        )



@app.command()
def cli(
    prompt: str = typer.Argument(..., help="Initial task description"),
) -> None:
    """Run the multi-agent pipeline with a user prompt."""
    import uuid
    import json
    from harnesscore.graph import build_graph
    from harnesscore.checkpointer.file_checkpointer import FileCheckpointer
    from harnesscore.schema import SystemState

    config = load_config()
    console.print(f"[bold]→[/] Starting HarnessCore CLI")
    console.print(f"  [dim]Prompt:[/dim] {prompt}")
    
    # Credentials check
    if not config.resolve_api_key():
        console.print(f"[bold red]Error:[/] API Key not set ({config.credentials.api_key_env})")
        raise typer.Exit(1)
        
    harness_dir = Path(config.project_root or ".") / ".harness"
    checkpointer = FileCheckpointer(harness_dir)
    app_graph = build_graph(config, checkpointer)
    
    thread_id = str(uuid.uuid4())
    config_dict = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": config.max_iterations
    }
    
    initial_state = SystemState(user_prompt=prompt)
    
    console.print(f"\n[cyan]Running Graph (Thread ID: {thread_id})...[/]\n")
    for s in app_graph.stream(initial_state, config_dict):
        for node_name, node_state in s.items():
            console.print(f"[bold green]▶ Node Finished: {node_name}[/]")
            
            # node_state might be a dict (update payload) or a SystemState instance
            if isinstance(node_state, dict):
                next_agent = node_state.get("next_agent", "UNKNOWN")
                logs = node_state.get("history_logs", [])
                if logs:
                    console.print(f"  [dim]Action:[/dim] {logs[-1].details}")
            else:
                next_agent = getattr(node_state, "next_agent", "UNKNOWN")
                logs = getattr(node_state, "history_logs", [])
                if logs:
                    console.print(f"  [dim]Action:[/dim] {logs[-1].details}")
                    
            console.print(f"  [dim]Routing To:[/dim] {next_agent}\n")
            
    console.print(f"[bold blue]✓ Workflow Finished.[/]")


@app.command()
def web(
    prompt: str = typer.Argument(..., help="Initial task description"),
    port: int = typer.Option(8000, help="Port for the web server"),
) -> None:
    """Launch Web mode: boot API engine and open browser dashboard."""
    console.print(f"[bold]→[/] Starting HarnessCore in [cyan]Web[/] mode on port {port}…")
    # TODO (Phase 4 / future): start FastAPI + open browser
    console.print("[yellow]Web mode not yet implemented.[/]")


if __name__ == "__main__":
    app()
