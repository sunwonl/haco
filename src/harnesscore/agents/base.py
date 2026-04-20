"""
Generic ReAct loop template for HarnessCore Agents.
Provides a unified pattern for executing tools and persisting conversational journals.
"""
import json
import uuid
from pathlib import Path
from typing import List, Callable, Dict, Any
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.language_models.chat_models import BaseChatModel

from harnesscore.schema import SystemState, JournalEntry, TokenUsage, TaskLog
from harnesscore.utils.journaler import Journaler

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

def run_agent_react_loop(
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

    # Inject Global Semantic Memory if exists
    mem_file = harness_dir / "memory.md"
    if mem_file.exists() and mem_file.stat().st_size > 0:
        global_memory_str = mem_file.read_text(encoding="utf-8")
        context_str += f"\n\n--- 🧠 GLOBAL LONG-TERM MEMORY ---\n{global_memory_str}\n--------------------------------"

    messages = [
        SystemMessage(content=sys_prompt),
        HumanMessage(content=context_str)
    ]
    
    new_journals = []
    
    # Defaults Fallback
    final_next_agent = "PO" if agent_name != "PO" else "HUMAN"
    final_new_tasks = {}
    completed_task_id = None
    
    loop_count = 0
    route_called = False
    
    print(f"[{agent_name}] Starting Conversational Loop...")
    
    while loop_count < max_loops:
        loop_count += 1
        response = llm_with_tools.invoke(messages)
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
        "history_logs": [log]
    }
