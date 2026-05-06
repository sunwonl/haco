import json
import os
import logging
import sys
import traceback
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from harnesscore.graph import build_graph
from harnesscore.checkpointer.file_checkpointer import FileCheckpointer
from harnesscore.config.loader import load_config
from harnesscore.schema import SystemState
from harnesscore.utils.runtime import RuntimeProfiler
from harnesscore.utils.memory_viewer import MemoryViewer
from harnesscore.utils.vector_store import LocalVectorStore

app = FastAPI()

# Configure logging to write to stderr for easier debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("harnesscore.web")

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


def _get_handoff_content(snapshot) -> str:
    """Extract the actual request content from the last agent in the history logs."""
    history = snapshot.values.get("history_logs", [])
    if not history:
        return snapshot.values.get("user_prompt", "")
    
    last_log = history[-1]
    msg = ""
    if isinstance(last_log, dict):
        msg = last_log.get("details", "")
    else:
        msg = getattr(last_log, "details", "")
    
    return msg if msg else snapshot.values.get("user_prompt", "")


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

    async def event_generator():
        try:
            # Initial "Thinking" state for the first assignee (usually PO)
            init_payload = {
                "type": "node_update",
                "node": "PO",
                "status": "thinking",
                "next_agent": None
            }
            yield f"data: {json.dumps(init_payload)}\n\n"

            async for event in app_graph.astream_events(input_state, config_dict, version="v2"):
                kind = event["event"]
                
                # A. Handle Real-time Content Streaming
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    content = ""
                    
                    # Extract and yield content parts
                    if hasattr(chunk, "content"):
                        raw_content = chunk.content
                        
                        # Case 1: Simple string
                        if isinstance(raw_content, str) and raw_content:
                            yield f"data: {json.dumps({'type': 'content_delta', 'content': raw_content})}\n\n"
                            
                        # Case 2: List of parts (common in multi-modal or thinking models)
                        elif isinstance(raw_content, list):
                            for part in raw_content:
                                if isinstance(part, str):
                                    yield f"data: {json.dumps({'type': 'content_delta', 'content': part})}\n\n"
                                elif isinstance(part, dict):
                                    ptype = part.get("type", "text")
                                    text = part.get("text", "")
                                    if text:
                                        # Map thought/reasoning types to our 'Thought' category
                                        cat = "Thought" if ptype in ["thought", "reasoning"] else "Message"
                                        yield f"data: {json.dumps({'type': 'content_delta', 'content': text, 'category': cat})}\n\n"
                        
                        # Case 3: Dictionary (fallback)
                        elif isinstance(raw_content, dict) and "text" in raw_content:
                            yield f"data: {json.dumps({'type': 'content_delta', 'content': raw_content['text']})}\n\n"

                # B. Handle Node Completion (State Updates)
                elif kind == "on_chain_end" and event["name"] in ["PO", "System Architect", "Core Developer", "QA Evaluator", "UI Engineer", "Design Reviewer"]:
                    node_name = event["name"]
                    node_state = event["data"]["output"]
                    if not node_state or not isinstance(node_state, dict):
                        continue
                    
                    next_agent = node_state.get("next_agent", "UNKNOWN")
                    log_objects = node_state.get("history_logs", [])
                    tasks = node_state.get("tasks", {})
                    file_changes = node_state.get("file_changes", [])

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

                    # If there's a next agent and it's not FINISH/HUMAN, proactively set it to "thinking"
                    if next_agent not in ["FINISH", "HUMAN", "UNKNOWN"]:
                        think_payload = {
                            "type": "node_update",
                            "node": next_agent,
                            "status": "thinking"
                        }
                        yield f"data: {json.dumps(think_payload)}\n\n"

            # Final snapshot for potential interrupts
            snapshot = app_graph.get_state(config_dict)
            if snapshot.next:
                hitl_payload = {
                    "type": "interrupt",
                    "next_node": snapshot.next[0],
                    "sender": snapshot.values.get("current_assignee", "PO"),
                    "content": _get_handoff_content(snapshot)
                }
                yield f"data: {json.dumps(hitl_payload)}\n\n"
                return

            yield f"data: {json.dumps({'type': 'finish'})}\n\n"
        except Exception as e:
            traceback.print_exc()
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
    async def resume_generator():
        try:
            async for event in app_graph.astream_events(None, config_dict, version="v2"):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    # Extract and yield content parts
                    if hasattr(chunk, "content"):
                        raw_content = chunk.content
                        if isinstance(raw_content, str) and raw_content:
                            yield f"data: {json.dumps({'type': 'content_delta', 'content': raw_content})}\n\n"
                        elif isinstance(raw_content, list):
                            for part in raw_content:
                                if isinstance(part, str):
                                    yield f"data: {json.dumps({'type': 'content_delta', 'content': part})}\n\n"
                                elif isinstance(part, dict):
                                    ptype = part.get("type", "text")
                                    text = part.get("text", "")
                                    if text:
                                        cat = "Thought" if ptype in ["thought", "reasoning"] else "Message"
                                        yield f"data: {json.dumps({'type': 'content_delta', 'content': text, 'category': cat})}\n\n"
                        elif isinstance(raw_content, dict) and "text" in raw_content:
                            yield f"data: {json.dumps({'type': 'content_delta', 'content': raw_content['text']})}\n\n"

                elif kind == "on_chain_end" and event["name"] in ["PO", "System Architect", "Core Developer", "QA Evaluator", "UI Engineer", "Design Reviewer"]:
                    node_name = event["name"]
                    node_state = event["data"]["output"]
                    if not node_state or not isinstance(node_state, dict):
                        continue
                        
                    next_agent = node_state.get("next_agent", "UNKNOWN")
                    log_objects = node_state.get("history_logs", [])
                    tasks = node_state.get("tasks", {})
                    file_changes = node_state.get("file_changes", [])

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
                hitl_payload = {
                    "type": "interrupt",
                    "next_node": snapshot.next[0],
                    "sender": snapshot.values.get("current_assignee", "PO"),
                    "content": _get_handoff_content(snapshot)
                }
                yield f"data: {json.dumps(hitl_payload)}\n\n"
                return

            yield f"data: {json.dumps({'type': 'finish'})}\n\n"
        except Exception as e:
            traceback.print_exc()
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

# ─── API: Runtime Stats ──────────────────────────────────────────────────────
@app.get("/api/runtime/{thread_id}")
async def get_runtime_stats(thread_id: str):
    """Returns detailed runtime and token stats for a specific thread."""
    config = load_config()
    harness_dir = _harness_dir()
    checkpointer = FileCheckpointer(harness_dir)
    app_graph = build_graph(config, checkpointer)

    config_dict = {"configurable": {"thread_id": thread_id}}
    state = app_graph.get_state(config_dict).values
    
    # Fallback to empty state if not found
    if not state:
        state = SystemState()
    else:
        # If it's a dict from checkpoint, parse it
        if isinstance(state, dict):
            state = SystemState(**state)

    return {
        "system": RuntimeProfiler.get_system_stats(),
        "usage": RuntimeProfiler.get_token_summary(state)
    }


# ─── API: Memory & Knowledge ────────────────────────────────────────────────
@app.get("/api/memory")
async def get_memory():
    """Returns project memory content and session timeline."""
    h_dir = _harness_dir()
    project_root = h_dir.parent
    return {
        "memory": MemoryViewer.get_memory_content(str(project_root)),
        "timeline": MemoryViewer.get_session_timeline(str(h_dir))
    }

@app.post("/api/memory/index")
async def index_memory():
    """Indexes memory.md sections into the local vector store."""
    try:
        from harnesscore.config import HarnessConfig
        config = HarnessConfig.load()
        h_dir = _harness_dir()
        project_root = h_dir.parent
        
        chunks = MemoryViewer.get_memory_chunks(str(project_root))
        if not chunks:
            return {"status": "success", "message": "No knowledge found to index."}
            
        store = LocalVectorStore(
            storage_dir=os.path.join(str(project_root), ".harness", "vectors"),
            api_key=config.google_api_key
        )
        
        # Clear old and add new
        store.clear()
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        await store.add_texts(texts, metadatas)
        
        return {"status": "success", "message": f"Indexed {len(chunks)} knowledge chunks."}
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


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
