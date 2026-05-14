"""
Configuration loader for .harness/settings.json.
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, List, Any

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
#  Sub-models                                                          #
# ------------------------------------------------------------------ #

class LLMConfig(BaseModel):
    """LLM provider and model selection."""

    provider: str = Field(
        default="google-genai",
        description="LLM provider ID (google-genai | google-vertexai | openai | anthropic | ollama)",
    )
    default_model: str = Field(
        default="gemini-3.1-flash-lite-preview",
        description="Model used by all agents unless overridden by agent_models",
    )
    agent_models: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Per-agent model overrides, e.g. "
            '{"PO": "gemini-2.5-pro", "QA Evaluator": "gemini-2.0-flash"}'
        ),
    )


class CredentialsConfig(BaseModel):
    """Authentication settings for cloud LLM providers."""

    api_key_env: str = Field(
        default="GEMINI_API_KEY",
        description="Name of the environment variable that holds the API key",
    )
    gcp_credentials_path: Optional[str] = Field(
        default=None,
        description="Path to a GCP service-account JSON file (leave null to use ADC)",
    )
    gcp_project: Optional[str] = Field(
        default=None,
        description="GCP Project ID (required for Vertex AI if not in creds file)",
    )
    gcp_location: str = Field(
        default="global",
        description="GCP region for Vertex AI",
    )


class GitConfig(BaseModel):
    """Git branch strategy settings."""

    base_branch: str = Field(
        default="main",
        description="Branch from which agent work-branches are created",
    )
    auto_commit: bool = Field(
        default=True,
        description="Automatically commit after each successful agent task",
    )


# ------------------------------------------------------------------ #
#  Root config                                                         #
# ------------------------------------------------------------------ #

class HarnessConfig(BaseModel):
    """Project-level configuration loaded from .harness/settings.json."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    credentials: CredentialsConfig = Field(default_factory=CredentialsConfig)
    git: GitConfig = Field(default_factory=GitConfig)

    project_root: Optional[str] = Field(
        default=None, description="Override project root (default: cwd)"
    )

    agent_paths: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Per-agent file-access root directories, e.g. "
            '{"Core Developer": "backend/", "UI Engineer": "frontend/"}'
        ),
    )
    max_iterations: int = Field(
        default=10,
        description="Maximum QA retry loops before HITL interrupt",
    )
    ignore_patterns: List[str] = Field(
        default_factory=lambda: [".git", "node_modules", "__pycache__", ".harness"],
        description="Path patterns excluded from agent file access",
    )
    mcp_servers: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description=(
            "Agent Name (or 'global') -> List of MCP server configs. "
            'Example: {"CD": [{"name": "github", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}]}'
        ),
    )
    language: str = Field(
        default="en",
        description="Language for journals and logs (en, ko, etc.)",
    )

    @property
    def harness_dir(self) -> Path:
        """Return the absolute path to the .harness directory."""
        root = Path(self.project_root) if self.project_root else Path.cwd()
        return root / ".harness"

    def model_for_agent(self, agent_name: str) -> str:
        """Return the model to use for *agent_name* (falls back to default)."""
        return self.llm.agent_models.get(agent_name, self.llm.default_model)

    def resolve_api_key(self) -> Optional[str]:
        """Read the API key from the configured environment variable or .env file."""
        # 1. Try environment first
        key = os.environ.get(self.credentials.api_key_env)
        if key and key.strip():
            return key
            
        # 2. Try .env in project root (or CWD) explicitly
        root = Path(self.project_root) if self.project_root else Path.cwd()
        env_path = root / ".env"
        
        if env_path.exists():
            try:
                from dotenv import load_dotenv
                # Use override=True to ensure .env values take precedence if environment is dirty
                load_dotenv(dotenv_path=env_path, override=True)
                key = os.environ.get(self.credentials.api_key_env)
                if not key:
                    print(f"  [Diagnostics] Found .env at {env_path}, but {self.credentials.api_key_env} is missing inside.")
                return key
            except ImportError:
                pass
        else:
            print(f"  [Diagnostics] No .env found at {env_path}")
        
        return None


# ------------------------------------------------------------------ #
#  Loader                                                              #
# ------------------------------------------------------------------ #

_DEFAULT_SETTINGS_PATH = Path(".harness") / "settings.json"


def load_config(path: Optional[Path] = None) -> HarnessConfig:
    """Load config from .harness/settings.json; bootstrap defaults if missing."""
    settings_path = path or _DEFAULT_SETTINGS_PATH
    if settings_path.exists():
        data = json.loads(settings_path.read_text())
        return HarnessConfig(**data)
    # First-run: write defaults and return them
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    config = HarnessConfig()
    settings_path.write_text(config.model_dump_json(indent=2))
    return config

LLMConfig.model_rebuild()
CredentialsConfig.model_rebuild()
GitConfig.model_rebuild()
HarnessConfig.model_rebuild()
