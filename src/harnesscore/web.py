import json
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from harnesscore.graph import build_graph
from harnesscore.checkpointer.file_checkpointer import FileCheckpointer
from harnesscore.config.loader import load_config
from harnesscore.schema import SystemState

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static Serving ─────────────────────────────────────────────────────────
# The frontend dist is relative to this web.py file which lives in src/harnesscore/
# src/harnesscore/web.py → root/frontend/dist
_frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

if _frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")

# ─── Helper: Resolve Harness dir ────────────────────────────────────────────
def _harness_dir() -> Path:
    """Use the directory where `harness web` was invoked (CWD) as the project root."""
    return Path(os.getcwd()) / ".harness"


# ─── API: Health Check ────────────────────────────────────────────────────────
@app.get("/api/health")
def health_check():
    """Simple liveness probe for the frontend health badge."""
    return {"status": "ok"}


# ─── API: Start or resume pipeline ──────────────────────────────────────────
@app.post("/api/run")
async def run_pipeline(request: Request):
    """Create a new thread or accept a resumed prompt."""
    data = await request.json()
    prompt = data.get("prompt", "")
    thread_id = data.get("thread_id") or str(uuid.uuid4())
    return {"thread_id": thread_id, "prompt": prompt}


# ─── API: SSE Event Stream ───────────────────────────────────────────────────
@app.get("/api/stream/{thread_id}")
def stream_pipeline(thread_id: str, prompt: str = "", resume: str = "false"):
    """Server-Sent Events endpoint to stream graph execution in real time."""
    config = load_config()

    if not config.resolve_api_key():
        def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'code': 'API_KEY_NOT_SET', 'message': f'Export {config.credentials.api_key_env} to run the engine.'})}\\n\\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    harness_dir = _harness_dir()
    checkpointer = FileCheckpointer(harness_dir)
    app_graph = build_graph(config, checkpointer)

    config_dict = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": config.max_iterations
    }

    if resume.lower() == "true":
        input_state = None
    else:
        existing_state = app_graph.get_state(config_dict)
        input_state = SystemState(user_prompt=prompt) if not existing_state.values else {"user_prompt": prompt}

    def event_generator():
        try:
            # Initial "Thinking" state for the first assignee (usually PO)
            # This helps UI show immediate feedback
            init_payload = {
                "type": "node_update",
                "node": "PO",
                "status": "thinking",
                "next_agent": None
            }
            yield f"data: {json.dumps(init_payload)}\n\n"

            for s in app_graph.stream(input_state, config_dict):
                for node_name, node_state in s.items():
                    if isinstance(node_state, dict):
                        next_agent = node_state.get("next_agent", "UNKNOWN")
                        log_objects = node_state.get("history_logs", [])
                        tasks = node_state.get("tasks", {})
                        file_changes = node_state.get("file_changes", [])
                    else:
                        next_agent = getattr(node_state, "next_agent", "UNKNOWN")
                        log_objects = getattr(node_state, "history_logs", [])
                        tasks = getattr(node_state, "tasks", {})
                        file_changes = getattr(node_state, "file_changes", [])

                    logs = [
                        {
                            "agent_name": log.agent_name,
                            "action_type": log.action_type,
                            "details": log.details,
                            "logs": log.logs,
                            "status": log.status
                        } if hasattr(log, "action_type") else log
                        for log in log_objects
                    ]

                    # Node finished -> Status: success
                    payload = {
                        "type": "node_update",
                        "node": node_name,
                        "next_agent": next_agent,
                        "status": "success",
                        "logs": logs,
                        "tasks": tasks,
                        "file_changes": file_changes
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                    # If there's a next agent and it's not FINISH/HUMAN, 
                    # we can proactively set it to "thinking"
                    if next_agent not in ["FINISH", "HUMAN", "UNKNOWN"]:
                        think_payload = {
                            "type": "node_update",
                            "node": next_agent,
                            "status": "thinking"
                        }
                        yield f"data: {json.dumps(think_payload)}\n\n"

                # Check for HUMAN-IN-THE-LOOP interrupt
                snapshot = app_graph.get_state(config_dict)
                if snapshot.next:
                    hitl_payload = {
                        "type": "interrupt",
                        "next_node": snapshot.next[0],
                    }
                    yield f"data: {json.dumps(hitl_payload)}\n\n"
                    return  # Stop streaming; client must POST /api/interrupt to resume

            yield f"data: {json.dumps({'type': 'finish'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─── API: HITL Interrupt Resume ──────────────────────────────────────────────
@app.get("/api/interrupt/{thread_id}")
async def resume_after_interrupt(thread_id: str, feedback: str = ""):
    """Resume the graph after a Human-In-The-Loop pause."""

    config = load_config()
    harness_dir = _harness_dir()
    checkpointer = FileCheckpointer(harness_dir)
    app_graph = build_graph(config, checkpointer)

    config_dict = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": config.max_iterations
    }

    # Patch the state if the user provided feedback
    if feedback:
        app_graph.update_state(config_dict, {"user_prompt": feedback})

    # Resume the graph from checkpoint (input=None signals continuation)
    def resume_generator():
        try:
            for s in app_graph.stream(None, config_dict):
                for node_name, node_state in s.items():
                    if isinstance(node_state, dict):
                        next_agent = node_state.get("next_agent", "UNKNOWN")
                        log_objects = node_state.get("history_logs", [])
                        tasks = node_state.get("tasks", {})
                        file_changes = node_state.get("file_changes", [])
                    else:
                        next_agent = getattr(node_state, "next_agent", "UNKNOWN")
                        log_objects = getattr(node_state, "history_logs", [])
                        tasks = getattr(node_state, "tasks", {})
                        file_changes = getattr(node_state, "file_changes", [])

                    logs = [
                        {
                            "agent_name": log.agent_name,
                            "action_type": log.action_type,
                            "details": log.details,
                            "logs": log.logs,
                            "status": log.status
                        } if hasattr(log, "action_type") else log
                        for log in log_objects
                    ]

                    yield f"data: {json.dumps({'type': 'node_update', 'node': node_name, 'next_agent': next_agent, 'logs': logs, 'tasks': tasks, 'file_changes': file_changes})}\n\n"

                snapshot = app_graph.get_state(config_dict)
                if snapshot.next:
                    yield f"data: {json.dumps({'type': 'interrupt', 'next_node': snapshot.next[0]})}\n\n"
                    return

            yield f"data: {json.dumps({'type': 'finish'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(resume_generator(), media_type="text/event-stream")


# ─── API: File System Explorer ───────────────────────────────────────────────
@app.get("/api/files")
def list_files(path: str = "."):
    """List CWD directory tree for the frontend File Explorer.
    
    Query params:
      path (str): Relative path from CWD to list. Defaults to '.'.
    Returns a list of file/directory entry objects.
    """
    cwd = Path(os.getcwd())
    target = (cwd / path).resolve()

    # Safety: prevent path traversal above CWD
    if not str(target).startswith(str(cwd)):
        return JSONResponse(status_code=403, content={"detail": "Access denied"})

    if not target.exists():
        return JSONResponse(status_code=404, content={"detail": "Path not found"})

    entries = []
    try:
        for entry in sorted(target.iterdir(), key=lambda e: (e.is_file(), e.name)):
            # Skip hidden dirs like .git, __pycache__ etc.
            if entry.name.startswith(".") or entry.name == "__pycache__":
                continue
            entries.append({
                "name": entry.name,
                "path": str(entry.relative_to(cwd)),
                "type": "directory" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else None,
            })
    except PermissionError:
        return JSONResponse(status_code=403, content={"detail": "Permission denied"})

    return {"path": str(target.relative_to(cwd)), "entries": entries}


@app.get("/api/files/content")
def get_file_content(path: str):
    """Return the text content of a file for the frontend Code Viewer.
    
    Query params:
      path (str): Relative path from CWD to the file.
    Returns content as plain text.
    """
    cwd = Path(os.getcwd())
    target = (cwd / path).resolve()

    if not str(target).startswith(str(cwd)):
        return JSONResponse(status_code=403, content={"detail": "Access denied"})

    if not target.exists() or not target.is_file():
        return JSONResponse(status_code=404, content={"detail": "File not found"})

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

    return {"path": str(target.relative_to(cwd)), "content": content}


# ─── API: State Snapshot ─────────────────────────────────────────────────────
@app.get("/api/state/{thread_id}")
def get_state(thread_id: str):
    """Return the full serialized state snapshot for a given thread.
    Allows the frontend to restore conversation history after a page refresh.
    """
    config = load_config()
    harness_dir = _harness_dir()
    checkpointer = FileCheckpointer(harness_dir)
    app_graph = build_graph(config, checkpointer)

    config_dict = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": config.max_iterations
    }

    try:
        snapshot = app_graph.get_state(config_dict)
        if not snapshot.values:
            return JSONResponse(status_code=404, content={"detail": "Thread not found"})

        state_values = snapshot.values
        if hasattr(state_values, "model_dump"):
            state_values = state_values.model_dump()

        return {
            "thread_id": thread_id,
            "next": list(snapshot.next),
            "state": state_values,
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


# ─── SPA Catch-All (must be last) ────────────────────────────────────────────
@app.get("/")
@app.get("/{catchall:path}")
def serve_frontend(catchall: str = ""):
    if catchall.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    file_path = _frontend_dist / catchall
    if _frontend_dist.exists() and file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    if _frontend_dist.exists():
        return FileResponse(_frontend_dist / "index.html")
    return JSONResponse(status_code=503, content={"detail": "Frontend not built. Run `npm run build` in frontend/"})
