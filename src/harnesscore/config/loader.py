"""
Configuration loader for .harness/settings.json.

On first run (`harness init`), this generates a default settings.json
and prompts the user to configure credentials via environment variables.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
#  Sub-models                                                          #
# ------------------------------------------------------------------ #

class LLMConfig(BaseModel):
    """LLM provider and model selection."""

    provider: str = Field(
        default="google-genai",
        description="LLM provider ID (google-genai | openai | anthropic | ollama)",
    )
    default_model: str = Field(
        default="gemini-2.0-flash",
        description="Model used by all agents unless overridden by agent_models",
    )
    agent_models: dict[str, str] = Field(
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

    agent_paths: dict[str, str] = Field(
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
    ignore_patterns: list[str] = Field(
        default_factory=lambda: [".git", "node_modules", "__pycache__", ".harness"],
        description="Path patterns excluded from agent file access",
    )
    mcp_servers: dict[str, str] = Field(
        default_factory=dict,
        description="MCP server name → endpoint URL",
    )

    # -------------------------------------------------------------- #
    #  Convenience helpers                                             #
    # -------------------------------------------------------------- #
    def model_for_agent(self, agent_name: str) -> str:
        """Return the model to use for *agent_name* (falls back to default)."""
        return self.llm.agent_models.get(agent_name, self.llm.default_model)

    def resolve_api_key(self) -> Optional[str]:
        """Read the API key from the configured environment variable."""
        return os.environ.get(self.credentials.api_key_env)


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
