"""
LLM Factory for instantiating models based on HarnessConfig.
"""
from __future__ import annotations

from typing import Annotated, Any

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from harnesscore.config.loader import HarnessConfig


def get_llm(config: HarnessConfig, agent_name: str, **kwargs: Any) -> BaseChatModel:
    """
    Instantiate the correct LangChain BaseChatModel based on config.
    """
    model_name = config.model_for_agent(agent_name)
    api_key = config.resolve_api_key()

    if not api_key:
        raise ValueError(
            f"API key not found. Ensure {config.credentials.api_key_env} is set "
            "before running HarnessCore agents."
        )

    if config.llm.provider == "google-genai":
        # Note: We support google-genai out of the box right now.
        return ChatGoogleGenerativeAI(
            model=model_name,
            api_key=api_key,
            **kwargs,
        )
    elif config.llm.provider == "openai":
        # Placeholder for OpenAI (requires langchain-openai)
        raise NotImplementedError("OpenAI provider requires installing `langchain-openai`.")
    else:
        raise NotImplementedError(f"Provider {config.llm.provider} is not yet supported.")
