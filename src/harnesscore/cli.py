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
from rich.console import Console

from harnesscore.config.loader import load_config

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
    """Launch TUI mode: boot API engine in background and open terminal UI."""
    console.print("[bold]→[/] Starting HarnessCore in [cyan]CLI/TUI[/] mode…")
    # TODO (Phase 4): boot FastAPI as daemon thread, then launch Textual app
    console.print("[yellow]TUI not yet implemented — coming in Phase 4.[/]")


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
