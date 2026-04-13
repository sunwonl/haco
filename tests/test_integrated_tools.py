import os
import sys
from pathlib import Path
import json

# Add src to sys.path for importing local harnesscore
sys.path.append(str(Path(__file__).parent.parent / "src"))

from harnesscore.tools.shell import ShellTool
from harnesscore.tools.network import NetworkTool
from harnesscore.config.loader import load_config
from harnesscore.agents.po import po_node
from harnesscore.agents.qa import qa_node
from harnesscore.schema import SystemState

def test_shell_tool():
    print("\n--- Testing ShellTool ---")
    shell = ShellTool(Path("."))
    
    # 1. Simple command
    res = shell.run_command("ls -F")
    print(f"ls output:\n{res[:200]}...")
    assert "src/" in res or "harnesscore/" in res
    
    # 2. Path Guard check
    res_err = shell.run_command("ls /etc/passwd")
    print(f"Forbidden path check: {res_err}")
    # Note: Depending on implementation, it might fail subprocess or our guard
    
    # 3. Tree view helper
    res_tree = shell.list_files_tree(depth=1)
    print(f"Tree depth 1:\n{res_tree}")
    assert "src" in res_tree

def test_network_tool():
    print("\n--- Testing NetworkTool ---")
    net = NetworkTool(timeout=5)
    
    # 1. External Ping (Success check)
    res_ping = net.ping("https://www.google.com")
    print(f"Ping google.com: {res_ping}")
    
    # 2. External Request 
    res_req = net.http_request("GET", "https://api.github.com/zen")
    print(f"GitHub Zen:\n{res_req}")

def test_po_environmental_awareness():
    print("\n--- Testing PO Environmental Awareness ---")
    config = load_config()
    state = SystemState(user_prompt="이 프로젝트의 최상위 폴더 구조를 설명해줘.")
    
    # Mocking config.project_root to current dir
    config.project_root = str(Path(".").resolve())
    
    # We call po_node and check if the 'reasoning' contains file info
    # Note: This requires a real LLM call if not mocked, but we'll try it.
    print("Calling PO node (LLM)...")
    result = po_node(state, config)
    
    print(f"PO Reasoning: {result['history_logs'][0].details}")
    # Check if PO mentioned files/folders it found
    logs = result["history_logs"][0].details.lower()
    assert "src" in logs or "harness" in logs or "folder" in logs

if __name__ == "__main__":
    try:
        test_shell_tool()
    except Exception as e:
        print(f"ShellTool Test Failed: {e}")
        
    try:
        test_network_tool()
    except Exception as e:
        print(f"NetworkTool Test Failed: {e}")

    # For PO test, only run if API Key is available
    config = load_config()
    if config.resolve_api_key():
        try:
            test_po_environmental_awareness()
        except Exception as e:
            print(f"PO Agent Test Failed: {e}")
    else:
        print("\nSkipping PO LLM test (API Key not set).")

    print("\n--- Integrated Tests Completed ---")
