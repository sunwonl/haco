"""
Generic ReAct loop template for HarnessCore Agents.
Provides a unified pattern for executing tools and persisting conversational journals.
"""
import json
import uuid
import time
import sys
import traceback
from pathlib import Path
from typing import List, Callable, Dict, Any
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.language_models.chat_models import BaseChatModel

from harnesscore.schema import SystemState, JournalEntry, TokenUsage, TaskLog
from harnesscore.utils.journaler import Journaler
from harnesscore.utils.vector_store import LocalVectorStore
from harnesscore.config.loader import load_config
import asyncio

def _ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def _extract_tokens(response) -> TokenUsage:
    meta = getattr(response, "usage_metadata", {})
    if not meta:
        return TokenUsage()
    return TokenUsage(
        input_tokens=meta.get("input_tokens", 0),
        output_tokens=meta.get("output_tokens", 0),
        thinking_tokens=meta.get("thinking_tokens", 0)
    )

async def run_agent_react_loop(
    agent_name: str,
    state: SystemState,
    llm: BaseChatModel,
    tools: List[Callable],
    sys_prompt: str,
    context_str: str,
    harness_dir: Path,
    max_loops: int = 10
) -> dict:
    """
    Executes a Conversational ReAct loop, updating the journal and state.
    The agent MUST use one of the terminating tools ('route_tasks', 'submit_work', 'route_agent') 
    to break the loop and define the next steps.
    """
    thread_id = getattr(state, "thread_id", str(uuid.uuid4())[:8])
    llm_with_tools = llm.bind_tools(tools)
    
    # Inject conversational memory into the context string
    recent_chat = []
    for je in state.journal[-30:]:
        if je.category == "Message":
            recent_chat.append(f"[{je.role}] {je.content}")
            
    if recent_chat:
        chat_history_str = "\n".join(recent_chat)
        context_str += f"\n\n--- Recent Conversation History ---\n{chat_history_str}"

    # Inject Global Semantic Memory if exists (Hybrid: Full or RAG-based)
    mem_file = harness_dir / "memory.md"
    if mem_file.exists() and mem_file.stat().st_size > 0:
        file_size = mem_file.stat().st_size
        # If the memory file is small (< 5KB), inject full content
        # Otherwise, perform vector search to keep context lean
        if file_size < 5000:
            global_memory_str = mem_file.read_text(encoding="utf-8")
            context_str += f"\n\n--- 🧠 GLOBAL LONG-TERM MEMORY ---\n{global_memory_str}\n--------------------------------"
        else:
            try:
                config = load_config()
                api_key = config.resolve_api_key()
                store = LocalVectorStore(
                    storage_dir=str(harness_dir / "vectors"),
                    api_key=api_key
                )
                
                # Use sync version to avoid event loop conflicts in sync nodes
                search_results = store.similarity_search_sync(context_str, k=5)
                
                if search_results:
                    rag_memory = "\n\n".join([f"[Relevance Score: {r['score']:.2f}]\n{r['text']}" for r in search_results])
                    context_str += f"\n\n--- 🧠 RELEVANT PROJECT MEMORY (RAG) ---\n{rag_memory}\n--------------------------------------"
                    print(f"[{agent_name}] Injected {len(search_results)} relevant chunks via RAG")
                else:
                    # Fallback to full if RAG is empty (index not built yet)
                    global_memory_str = mem_file.read_text(encoding="utf-8")
                    context_str += f"\n\n--- 🧠 GLOBAL LONG-TERM MEMORY (Fallback) ---\n{global_memory_str}\n--------------------------------"
            except Exception as e:
                print(f"[{agent_name}] Warning: RAG Retrieval failed, falling back to full memory. ({e})")
                global_memory_str = mem_file.read_text(encoding="utf-8")
                context_str += f"\n\n--- 🧠 GLOBAL LONG-TERM MEMORY (Error Fallback) ---\n{global_memory_str}\n--------------------------------"

    # Inject Active Skills & Protocols
    skills_dir = harness_dir / "skills"
    if skills_dir.exists() and skills_dir.is_dir():
        skills_content = []
        # Normalize agent name for filename matching (e.g., "Core Developer" -> "core_developer")
        norm_name = agent_name.lower().replace(" ", "_")
        
        # Sort files to ensure stable prompt order
        for skill_file in sorted(skills_dir.glob("*.md")):
            fname = skill_file.stem.lower()
            if fname in ["global", "common", norm_name]:
                try:
                    skill_text = skill_file.read_text(encoding="utf-8")
                    skills_content.append(f"### SKILL: {skill_file.stem.upper()}\n{skill_text}")
                except Exception as e:
                    print(f"[{agent_name}] Warning: Failed to read skill {skill_file.name}: {e}")
        
        if skills_content:
            combined_skills = "\n\n".join(skills_content)
            context_str += f"\n\n--- 🛠️ ACTIVE SKILLS & PROTOCOLS ---\n{combined_skills}\n-----------------------------------"
            print(f"[{agent_name}] Injected {len(skills_content)} skills from .harness/skills/")

    # Force Korean response in the system prompt
    kor_enforcement = "\n\nCRITICAL: Always respond in Korean (한국어). Use professional and polite language."
    full_sys_prompt = sys_prompt + kor_enforcement

    messages = [
        SystemMessage(content=full_sys_prompt),
        HumanMessage(content=context_str)
    ]
    
    new_journals = []
    
    # Defaults Fallback
    final_next_agent = "PO" if agent_name != "PO" else "HUMAN"
    final_new_tasks = {}
    completed_task_id = None
    
    loop_count = 0
    route_called = False
    loop_tokens = TokenUsage()
    
    print(f"[{agent_name}] Starting Conversational Loop...")
    
    while loop_count < max_loops:
        loop_count += 1
        
        # LLM Invoke with simple 429 retry
        response = None
        max_retries = 5
        base_delay = 2
        for attempt in range(max_retries):
            try:
                # Use astream for real-time tracking if caller uses astream_events
                full_response = None
                async for chunk in llm_with_tools.astream(messages):
                    if full_response is None:
                        full_response = chunk
                    else:
                        full_response += chunk
                response = full_response
                loop_tokens += _extract_tokens(response)
                break
            except Exception as e:
                print(f"[{agent_name}] Error invoking LLM (Attempt {attempt+1}/{max_retries}): {e}", file=sys.stderr)
                err_str = str(e).lower()
                if "429" in err_str or "resource_exhausted" in err_str:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"[{agent_name}] LLM Rate Limit (429) hit. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                raise e # Re-raise if not a rate limit error
        
        if not response:
            print(f"[{agent_name}] Max retries exceeded for LLM call.")
            break
            
        messages.append(response)
        
        # A. Log Thought
        if response.content:
            content_str = response.content
            if isinstance(content_str, list):
                # Extract text blocks, fallback to string representation
                text_parts = [item.get("text", "") for item in content_str if isinstance(item, dict) and "text" in item]
                content_str = "\n".join(text_parts) if text_parts else str(content_str)
                
            import os
            if isinstance(content_str, str) and content_str.strip():
                if os.environ.get("HARNESS_DEBUG") == "1":
                    from rich.console import Console
                    Console().print(f"[dim italic][Debug: {agent_name} Thought][/]\n[dim]{content_str}[/]")
                je_thought = JournalEntry(
                    timestamp=_ts(), session_id=thread_id, role=agent_name, category="Thought",
                    content=content_str, tokens=_extract_tokens(response)
                )
                new_journals.append(je_thought)
                Journaler.append_entry(harness_dir, je_thought.model_dump())
            
        if not response.tool_calls:
            # If the LLM just talks without using tools, we assume it's stuck or finished implicitly
            break
            
        for tool_call in response.tool_calls:
            t_name = tool_call["name"]
            t_args = tool_call["args"]
            
            import os
            if os.environ.get("HARNESS_DEBUG") == "1":
                from rich.console import Console
                Console().print(f"[magenta][Debug: {agent_name} Action][/] {t_name} -> {t_args}")

            # B. Log Action
            je_action = JournalEntry(
                timestamp=_ts(), session_id=thread_id, role=agent_name, category="Action",
                target=t_name, content=json.dumps(t_args, ensure_ascii=False)
            )
            new_journals.append(je_action)
            Journaler.append_entry(harness_dir, je_action.model_dump())
            
            # C. Execute Tool
            tool_fn = next((t for t in tools if t.__name__ == t_name), None)
            tool_result = ""
            if tool_fn:
                try:
                    tool_result = tool_fn(**t_args)
                except Exception as e:
                    tool_result = f"Error executing tool: {e}"
            else:
                tool_result = "Unknown tool."
                
            messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))
            
            # D. Handle Terminating Tools
            if t_name in ["route_tasks", "submit_work"]:
                final_next_agent = t_args.get("next_agent", "PO")
                msg_content = t_args.get("message") or t_args.get("response", "")
                completed_task_id = t_args.get("completed_task_id")
                
                try:
                    tasks_raw = t_args.get("new_tasks", "{}")
                    final_new_tasks = json.loads(tasks_raw) if isinstance(tasks_raw, str) else tasks_raw
                except:
                    pass
                
                # Log Message to Next Agent
                target_str = final_next_agent
                if final_next_agent == "FINISH":
                    target_str = "User"
                    
                je_msg = JournalEntry(
                    timestamp=_ts(), session_id=thread_id, role=agent_name, category="Message",
                    target=target_str, content=msg_content
                )
                new_journals.append(je_msg)
                Journaler.append_entry(harness_dir, je_msg.model_dump())
                route_called = True
                break
            
            # E. Log Result for Non-Terminating Tools
            if not route_called:
                res_content = str(tool_result)[:500] + ("..." if len(str(tool_result))>500 else "")
                
                if os.environ.get("HARNESS_DEBUG") == "1":
                    Console().print(f"[cyan][Debug: {agent_name} Result][/] {res_content}")

                je_result = JournalEntry(
                    timestamp=_ts(), session_id=thread_id, role=agent_name, category="Result",
                    content=res_content
                )
                new_journals.append(je_result)
                Journaler.append_entry(harness_dir, je_result.model_dump())
                
        if route_called:
            break
            
    # Process return state modifications
    updated_tasks = dict(state.tasks)
    updated_tasks.update(final_new_tasks)
    
    updated_completed = list(state.completed_tasks)
    if completed_task_id and completed_task_id not in updated_completed:
        # Check if the completed task exists in the current queue to avoid ghost entries
        if completed_task_id in updated_tasks:
            updated_completed.append(completed_task_id)
            # Remove from pending queue effectively by it being in completed
    
    # Extract recent thought and message for the Legacy wrapper (used by CLI UI)
    latest_thought = ""
    latest_msg = f"Terminated -> {final_next_agent}"
    
    for je in new_journals:
        if je.category == "Thought":
            latest_thought = je.content
        elif je.category == "Message":
            latest_msg = je.content

    # If the agent didn't successfully route via a tool, their raw thought is their final response
    if not route_called and latest_thought:
        latest_msg = latest_thought
        latest_thought = "Implicit termination (No tools called)."

    # Legacy wrapper
    log = TaskLog(
        agent_name=agent_name, action_type="EXECUTION",
        details=latest_msg,
        logs=latest_thought,
        status="SUCCESS"
    )
    
    return {
        "current_assignee": agent_name,
        "next_agent": final_next_agent,
        "tasks": updated_tasks,
        "completed_tasks": updated_completed,
        "journal": new_journals,
        "history_logs": [log],
        "total_tokens": loop_tokens
    }
