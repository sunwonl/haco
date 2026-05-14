import json
import functools
from typing import List, Dict, Any, Callable
from harnesscore.mcp.client import MCPClient
from harnesscore.config.loader import HarnessConfig

# Global registry to keep track of active MCP clients for reuse
_client_cache: Dict[str, MCPClient] = {}

def get_mcp_tools(agent_name: str, config: HarnessConfig) -> List[Callable]:
    """
    Discovers and wraps MCP tools for a specific agent. Reuses existing clients if possible.
    """
    global _client_cache
    tools = []
    
    # 1. Identify relevant MCP servers
    servers_to_load = []
    if "global" in config.mcp_servers:
        for s in config.mcp_servers["global"]:
            s["_origin"] = "global"
            servers_to_load.append(s)
    if agent_name in config.mcp_servers:
        for s in config.mcp_servers[agent_name]:
            s["_origin"] = agent_name
            servers_to_load.append(s)
        
    # 2. Load/Reuse servers and create tool wrappers
    for s_conf in servers_to_load:
        name = s_conf.get("name", "unknown")
        cmd = s_conf.get("command")
        args = s_conf.get("args", [])
        if not cmd: continue
            
        # Create a unique key for this server configuration
        cache_key = f"{cmd} {' '.join(args)}"
        
        client = _client_cache.get(cache_key)
        if not client:
            client = MCPClient(name, cmd, args)
            try:
                client.start()
                _client_cache[cache_key] = client
            except Exception as e:
                print(f"  [MCP] Error starting {name}: {e}")
                continue
        
        # 3. Create tool wrappers from the client
        try:
            mcp_tools = client.list_tools()
            for t_info in mcp_tools:
                t_name = t_info["name"]
                t_desc = t_info.get("description", "No description provided.")
                
                # Collision avoidance: mcp_{server_name}_{tool_name}
                wrapper_name = f"mcp_{name}_{t_name}"
                
                def create_wrapper(c, original_name, w_name, desc):
                    # We need to capture the current state in the closure
                    async def mcp_wrapper(**kwargs):
                        return c.call_tool(original_name, kwargs)
                    
                    mcp_wrapper.__name__ = w_name
                    mcp_wrapper.__doc__ = f"[MCP Tool from {name}] {desc}"
                    return mcp_wrapper
                
                tools.append(create_wrapper(client, t_name, wrapper_name, t_desc))
                
        except Exception as e:
            print(f"  [MCP] Error listing tools from {name}: {e}")
            
    return tools

def shutdown_mcp_clients():
    """Stops all active MCP server processes."""
    global _client_cache
    for client in _client_cache.values():
        client.stop()
    _client_cache.clear()
