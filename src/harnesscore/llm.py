"""
LLM Factory for instantiating models based on HarnessConfig.
"""
from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from harnesscore.config.loader import HarnessConfig
from harnesscore.schema import TokenUsage


def get_llm(config: HarnessConfig, agent_name: str, **kwargs: Any) -> BaseChatModel:
    """
    Instantiate the correct LangChain BaseChatModel based on config.
    """
    model_name = config.model_for_agent(agent_name)
    provider = config.llm.provider

    if provider == "google-genai":
        api_key = config.resolve_api_key()
        if not api_key:
            raise ValueError(
                f"API key not found for {provider}. Ensure {config.credentials.api_key_env} is set."
            )
        return ChatGoogleGenerativeAI(
            model=model_name,
            api_key=api_key,
            **kwargs,
        )

    elif provider == "google-vertexai":
        from langchain_google_vertexai import ChatVertexAI
        
        creds = None
        if config.credentials.gcp_credentials_path:
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_file(
                config.credentials.gcp_credentials_path
            )
        
        return ChatVertexAI(
            model=model_name,
            project=config.credentials.gcp_project,
            location=config.credentials.gcp_location,
            credentials=creds,
            **kwargs,
        )

    elif provider == "openai":
        api_key = config.resolve_api_key()
        if not api_key:
            raise ValueError(f"API key not found for {provider}.")
        # Placeholder for OpenAI (requires langchain-openai)
        raise NotImplementedError("OpenAI provider requires installing `langchain-openai`.")

    else:
        raise NotImplementedError(f"Provider {provider} is not yet supported.")


def extract_token_usage(response: Any) -> TokenUsage:
    """
    Extract token usage data from a LangChain LLM response.
    Supports both BaseMessage (raw) and structured output wrappers.
    """
    usage = TokenUsage()
    
    # Handle raw response metadata (LangChain usage_metadata)
    metadata = getattr(response, "usage_metadata", {})
    
    # Fallback for some older versions or different providers
    if not metadata and hasattr(response, "response_metadata"):
        metadata = response.response_metadata.get("token_usage", {})
    
    if metadata:
        usage.input_tokens = metadata.get("input_tokens") or metadata.get("prompt_tokens") or 0
        usage.output_tokens = metadata.get("output_tokens") or metadata.get("completion_tokens") or 0
        
        # Thinking/Reasoning tokens (Gemini specific or others)
        # Note: 'thinking_tokens' is a common field for Gemini reasoning models.
        usage.thinking_tokens = metadata.get("thinking_tokens") or 0
        
    return usage
