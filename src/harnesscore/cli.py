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
from rich.panel import Panel
from rich.text import Text

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
    harness_dir = Path(".harness")
    harness_dir.mkdir(exist_ok=True)
    
    config = load_config()

    console.print(
        f"\n[bold green]HarnessCore Initialization[/]\n"
        f"  [bold]•[/] Config Directory : [cyan]{harness_dir}/[/]\n"
        f"  [bold]•[/] Default Provider : [cyan]{config.llm.provider}[/]\n"
        f"  [bold]•[/] Default Model    : [cyan]{config.llm.default_model}[/]"
    )

    # 1. .env Template creation
    env_file = Path(".env")
    if not env_file.exists():
        console.print("  [bold]•[/] Creating [bold].env[/] template...")
        env_file.write_text(f"{config.credentials.api_key_env}=your_api_key_here\n")
        console.print("    [dim](Please edit .env and add your real API key)[/]")
    else:
        console.print("  [bold]•[/] [bold].env[/] already exists.")

    # 2. Git check
    git_dir = Path(".git")
    if not git_dir.exists():
        console.print("\n[bold yellow]⚠[/] Git not initialized. Agents strongly prefer working in a Git repository.")
        console.print("  Run [dim]git init[/] to enable automatic commits and rollbacks.")
    else:
        console.print("  [bold]•[/] Git repository detected. ✅")

    # 3. Instructions bootstrapping
    from harnesscore.utils.prompt_manager import PromptManager
    instr_dir = harness_dir / "instructions"
    if not instr_dir.exists():
        console.print("  [bold]•[/] Bootstrapping agent [bold]instructions/[/]...")
        instr_dir.mkdir(exist_ok=True)
        templates = PromptManager.get_default_templates()
        for agent_id, content in templates.items():
            tpl_file = instr_dir / f"{agent_id}.md"
            tpl_file.write_text(content, encoding="utf-8")
    else:
        console.print("  [bold]•[/] [bold]instructions/[/] already exists.")

    # 4. Final instruction

    console.print(
        f"\n[bold green]✓[/] Project ready! Run your first agent with:\n"
        f"  [cyan]harness cli \"Hello, analyze this project\"[/]\n"
    )

@app.command()
def reset(
    no_backup: bool = typer.Option(False, "--no-backup", help="Skip creating a backup of .harness folder"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation prompt"),
) -> None:
    """Completely wipe the .harness/ directory and re-initialize with defaults."""
    import shutil
    import datetime
    
    harness_dir = Path(".harness")
    if not harness_dir.exists():
        console.print("[yellow]No .harness directory found. Nothing to reset.[/]")
        return

    if not yes:
        confirm = typer.confirm("This will delete all configurations, agent instructions, and journals. Proceed?", default=False)
        if not confirm:
            console.print("[red]Aborted.[/]")
            raise typer.Abort()

    # Backup
    if not no_backup:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f".harness_backup_{timestamp}")
        console.print(f"  [bold]•[/] Backing up existing configuration to [cyan]{backup_dir}/[/]...")
        try:
            shutil.move(str(harness_dir), str(backup_dir))
        except Exception as e:
            console.print(f"[bold red]Backup failed:[/] {e}")
            raise typer.Exit(1)
    else:
        # Delete
        console.print(f"  [bold]•[/] Wiping [cyan]{harness_dir}/[/]...")
        try:
            shutil.rmtree(str(harness_dir))
        except Exception as e:
            console.print(f"[bold red]Wipe failed:[/] {e}")
            raise typer.Exit(1)

    # Re-initialize
    console.print("  [bold]•[/] [bold green]Re-initializing environment...[/]")
    init()


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
def chat() -> None:
    """Interactive mode to chat with HarnessCore agents."""
    import uuid
    from harnesscore.graph import build_graph
    from harnesscore.checkpointer.file_checkpointer import FileCheckpointer
    from harnesscore.schema import SystemState
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style

    config = load_config()
    console.print(f"\n[bold green]HarnessCore Interactive REPL[/]")
    console.print(f"[dim]Type 'exit' or 'quit' to end session, '/reset' to start fresh.[/]\n")
    
    # Credentials check
    if not config.resolve_api_key():
        console.print(f"[bold red]Error:[/] API Key not set ({config.credentials.api_key_env})")
        raise typer.Exit(1)
        
    harness_dir = Path(config.project_root or ".") / ".harness"
    checkpointer = FileCheckpointer(harness_dir)
    app_graph = build_graph(config, checkpointer)
    
    # Session setup
    thread_id = str(uuid.uuid4())
    config_dict = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": config.max_iterations
    }
    
    # Prompt Toolkit Setup
    session = PromptSession(history=InMemoryHistory())
    style = Style.from_dict({
        'prompt': 'ansicyan bold',
    })

    has_active_state = False

    while True:
        try:
            # use prompt_toolkit for better experience (multibyte/IME support)
            user_input = session.prompt([('class:prompt', 'User > ')], style=style).strip()
            
            if not user_input:
                continue

            # Command handling
            if user_input.startswith("/"):
                cmd = user_input.lower()
                if cmd in ["/quit", "/exit"]:
                    break
                elif cmd == "/reset":
                    thread_id = str(uuid.uuid4())
                    config_dict["configurable"]["thread_id"] = thread_id
                    has_active_state = False
                    console.print("[yellow]Session reset with new Thread ID.[/]")
                    continue
                elif cmd == "/help":
                    console.print("\n[bold]HarnessCore REPL Commands:[/]")
                    console.print("  [cyan]/help[/]   - Show this help message")
                    console.print("  [cyan]/reset[/]  - Reset the current session state")
                    console.print("  [cyan]/quit[/]   - Exit the REPL")
                    console.print("  [cyan]/exit[/]   - Exit the REPL\n")
                    continue
                else:
                    console.print(f"[yellow]Unknown command: {user_input}. Type /help for assistance.[/]")
                    continue
            
            # Prevent accidental plain "quit"/"exit" from stopping the loop 
            # while still allowing them to be spoken to the agent if desired?
            # User said: "일반 언어와 명령어를 구분할 수 있게 해야겠어"
            # So I'll only treat / commands as system commands.

            if not has_active_state:
                current_state = SystemState(user_prompt=user_input)
            else:
                # When resuming or sending new message, we update the user_prompt
                current_state = {"user_prompt": user_input}

            console.print(f"\n[dim]Agent working... (Thread: {thread_id})[/]")
            
            # The run loop needs to handle interrupts
            while True:
                last_node = None
                stop_reason = "FINISH"

                for s in app_graph.stream(current_state, config_dict):
                    for node_name, node_state in s.items():
                        last_node = node_name
                        
                        if isinstance(node_state, dict):
                            logs = node_state.get("history_logs", [])
                            next_agent = node_state.get("next_agent", "UNKNOWN")
                        else:
                            logs = getattr(node_state, "history_logs", [])
                            next_agent = getattr(node_state, "next_agent", "UNKNOWN")

                        if logs:
                            last_log = logs[-1]
                            agent_name = last_log.agent_name if hasattr(last_log, "agent_name") else last_log.get("agent_name", node_name)
                            details = last_log.details if hasattr(last_log, "details") else last_log.get("details", "")
                            thinking = last_log.logs if hasattr(last_log, "logs") else last_log.get("logs", "")

                            # Role-based coloring map
                            COLOR_MAP = {
                                "PO": "green",
                                "Product Owner": "green",
                                "System Architect": "magenta",
                                "SA": "magenta",
                                "Core Developer": "cyan",
                                "CD": "cyan",
                                "UI Engineer": "cyan",
                                "UI": "cyan",
                                "QA Evaluator": "yellow",
                                "QA": "yellow",
                                "Design Reviewer": "yellow",
                                "DR": "yellow"
                            }
                            agent_color = COLOR_MAP.get(agent_name, "blue")

                            # 1. Thinking Process (Reasoning)
                            if thinking:
                                console.print(Panel(
                                    Text(thinking, style="dim italic"),
                                    title=f"🔍 {agent_name} Thinking",
                                    border_style="bright_black",
                                    padding=(0, 1)
                                ))

                            # 2. Response (Direct message)
                            console.print(Panel(
                                Text(details, style=f"bold {agent_color}"),
                                title=f"💬 {agent_name} Response",
                                border_style=agent_color,
                                padding=(1, 2)
                            ))

                        if next_agent == "FINISH":
                             console.print(f"\n[bold blue]✓ Workflow Complete.[/]\n")
                        elif next_agent == "HUMAN":
                             console.print(f"\n[bold yellow]✋ Agent is waiting for your input...[/]\n")
                             stop_reason = "HUMAN"
                        else:
                             console.print(f"  [dim]Preparing handoff to:[/dim] [bold]{next_agent}[/]\n")
                
                # Check if we hit an interrupt (breakpoint)
                snapshot = app_graph.get_state(config_dict)
                if snapshot.next:
                    # We are at a breakpoint (interrupt_before)
                    next_node = snapshot.next[0]
                    state_at_break = snapshot.values
                    
                    # Diagnostic display for HITL
                    console.print("\n" + "="*50)
                    console.print(f"[bold yellow]✋ HITL Approval Required[/]")
                    
                    # 1. What just happened?
                    logs = state_at_break.get("history_logs", [])
                    if logs:
                        last_log = logs[-1]
                        # Handle both object and dict access (LangGraph state recovery can return dicts)
                        try:
                            agent_name = last_log.agent_name if hasattr(last_log, "agent_name") else last_log.get("agent_name", "Unknown")
                            details = last_log.details if hasattr(last_log, "details") else last_log.get("details", "N/A")
                            console.print(f"[bold blue]Previous Action ({agent_name}):[/] {details}")
                        except:
                            console.print(f"[bold blue]Previous Action:[/] (Detail expansion failed)")
                    
                    # 2. What is next?
                    console.print(f"[bold green]Next Plan:[/] Prepare to execute [bold cyan]{next_node}[/].")
                    
                    # 3. Pending Tasks
                    tasks = state_at_break.get("tasks", {})
                    completed = state_at_break.get("completed_tasks", [])
                    pending = [desc for tid, desc in tasks.items() if tid not in completed]
                    if pending:
                        console.print(f"[bold]Pending Tasks ({len(pending)}):[/]")
                        for p in pending[:3]:
                            console.print(f"  - {p}")
                        if len(pending) > 3:
                            console.print(f"  - ... and {len(pending)-3} more")
                    
                    console.print("="*50)
                    console.print(f"[dim](Type 'yes' to approve, 'no' to stop, or provide manual instructions to redirect the agents)[/]")
                    
                    user_feedback = session.prompt([('class:prompt', 'Approval > ')], style=style).strip()
                    if not user_feedback or user_feedback.lower() in ["yes", "y", "ok"]:
                        # Continue as is
                        current_state = None 
                        continue 
                    elif user_feedback.lower() in ["no", "n", "stop", "exit"]:
                        break
                    else:
                        # Feed the instructions into the next state
                        current_state = {"user_prompt": user_feedback}
                        continue
                else:
                    # Graph finished or reached HUMAN state (which we mapped to END)
                    break 
                    
            has_active_state = True 
            console.print("")


        except KeyboardInterrupt:
            continue # Don't exit on Ctrl+C in REPL
        except EOFError:
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")

    console.print(f"\n[bold blue]HarnessCore session ended.[/]")


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
