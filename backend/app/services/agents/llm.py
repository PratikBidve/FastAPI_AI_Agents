"""
LLM configuration and utilities for the Job Copilot agent.
Handles LLM initialization and provides reusable components.
"""

import os

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for LLM instances."""

    model_name: str = Field(default="gpt-4-turbo", description="OpenAI model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    api_key: str | None = Field(default=None)


class LLMProvider:
    """
    Central provider for LLM instances.
    Implements singleton pattern for efficient resource management.
    """

    _instance: "LLMProvider" | None = None
    _llm: ChatOpenAI | None = None
    _config: LLMConfig | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init(self, config: LLMConfig | None = None) -> None:
        """Initialize the LLM provider with configuration."""
        if config is None:
            config = LLMConfig(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_name=os.getenv("LLM_MODEL", "gpt-4-turbo"),
                temperature=float(os.getenv("LLM_TEMPERATURE", 0.7)),
                max_tokens=None,
            )

        self._config = config
        self._llm = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            api_key=config.api_key or os.getenv("OPENAI_API_KEY"),
        )

    def get_llm(self) -> ChatOpenAI:
        """Get the LLM instance. Initialize if needed."""
        if self._llm is None:
            self.init()
        return self._llm

    def get_config(self) -> LLMConfig:
        """Get current LLM configuration."""
        if self._config is None:
            self.init()
        return self._config


# Singleton instance
llm_provider = LLMProvider()


def get_llm() -> ChatOpenAI:
    """Convenience function to get the current LLM instance."""
    return llm_provider.get_llm()


def init_llm(config: LLMConfig | None = None) -> ChatOpenAI:
    """Initialize and return LLM instance."""
    llm_provider.init(config)
    return llm_provider.get_llm()
