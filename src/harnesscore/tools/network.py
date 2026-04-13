"""
Network and API testing tools for agents.
Provides basic HTTP request capabilities and health check (ping) tools.
"""
import urllib.request
import urllib.error
import json
import time
from typing import Optional, Dict, Any, Union


class NetworkTool:
    """
    Tool for interacting with web services and checking API health.
    Useful for QA Evaluators to verify running servers.
    """

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def ping(self, url: str) -> str:
        """
        Perform a simple GET request to check if a URL is reachable.
        
        Args:
            url: The URL to check (e.g., 'http://localhost:8000/health').
            
        Returns:
            Status message with response code or error.
        """
        try:
            start_time = time.time()
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                duration = (time.time() - start_time) * 1000
                return f"SUCCESS: {url} is reachable. Status: {response.status}. Latency: {duration:.2f}ms"
        except urllib.error.HTTPError as e:
            return f"FAIL: {url} returned HTTP Error {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return f"FAIL: {url} is unreachable. Reason: {e.reason}"
        except Exception as e:
            return f"ERROR: Unexpected failure pinging {url}: {str(e)}"

    def http_request(
        self, 
        method: str, 
        url: str, 
        data: Optional[Dict[str, Any]] = None, 
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Perform a generic HTTP request (GET, POST, etc.).
        
        Args:
            method: 'GET', 'POST', 'PUT', 'DELETE'.
            url: The target URL.
            data: Optional dictionary to send as JSON in the body.
            headers: Optional dictionary of HTTP headers.
            
        Returns:
            String representation of the response (Status + Body summary).
        """
        method = method.upper()
        req_headers = headers or {}
        
        # Prepare data
        body = None
        if data:
            body = json.dumps(data).encode("utf-8")
            if "Content-Type" not in req_headers:
                req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                resp_data = response.read().decode("utf-8")
                try:
                    # Try to pretty-print if it's JSON
                    parsed = json.loads(resp_data)
                    summary = json.dumps(parsed, indent=2, ensure_ascii=False)
                except:
                    summary = resp_data[:1000] + ("..." if len(resp_data) > 1000 else "")
                
                return f"--- Response ({response.status}) ---\n{summary}"
        except urllib.error.HTTPError as e:
            return f"Error: HTTP {e.code} - {e.read().decode('utf-8')}"
        except Exception as e:
            return f"Error: Request failed: {str(e)}"
