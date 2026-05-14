import json
import subprocess
import threading
from typing import Dict, List, Any, Optional
from pathlib import Path

class MCPClient:
    """A simple stdio-based MCP client to communicate with external MCP servers."""

    def __init__(self, name: str, command: str, args: List[str]):
        self.name = name
        self.command = command
        self.args = args
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 1
        self._lock = threading.Lock()

    def start(self):
        """Starts the MCP server process."""
        print(f"  [MCP] Starting server '{self.name}': {self.command} {' '.join(self.args)}")
        try:
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            # Initialize connection
            self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "HarnessCore", "version": "0.1.0"}
            })
            self._send_notification("notifications/initialized", {})
            print(f"  [MCP] Server '{self.name}' initialized.")
        except Exception as e:
            print(f"  [MCP] Failed to start server '{self.name}': {e}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Fetch the list of tools from the MCP server."""
        response = self._send_request("tools/list", {})
        return response.get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on the MCP server."""
        return self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

    def stop(self):
        """Terminates the MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            print(f"  [MCP] Server '{self.name}' stopped.")

    def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sends a JSON-RPC request and waits for the response."""
        if not self.process or not self.process.stdin:
            return {"error": "Process not started"}

        with self._lock:
            req_id = self._request_id
            self._request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params
            }
            
            # Write request
            json.dump(request, self.process.stdin)
            self.process.stdin.write("\n")
            self.process.stdin.flush()

            # Read response
            line = self.process.stdout.readline()
            if not line:
                return {"error": "No response from server"}
            
            try:
                response = json.loads(line)
                if response.get("id") != req_id:
                    # Handle async notifications or mismatched IDs if necessary
                    return {"error": "Mismatched request ID"}
                return response.get("result", {})
            except Exception as e:
                return {"error": f"Failed to parse response: {e}"}

    def _send_notification(self, method: str, params: Dict[str, Any]):
        """Sends a JSON-RPC notification (no response expected)."""
        if not self.process or not self.process.stdin:
            return
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        json.dump(request, self.process.stdin)
        self.process.stdin.write("\n")
        self.process.stdin.flush()
