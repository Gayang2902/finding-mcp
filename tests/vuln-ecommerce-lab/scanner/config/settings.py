"""
Scanner configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main scanner configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Target
    target_url: str = Field(
        default="http://localhost:8080/api",
        description="Base URL of the target API",
    )

    # LLM
    llm_base_url: str = Field(
        default="http://localhost:11434/v1",
        description="OpenAI-compatible LLM endpoint (ollama default)",
    )
    llm_model: str = Field(
        default="llama3:8b",
        description="Model name to use for analysis",
    )
    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM sampling temperature",
    )
    llm_max_tokens: int = Field(
        default=4096,
        description="Max tokens per LLM response",
    )
    llm_api_key: str = Field(
        default="ollama",
        description="API key (use 'ollama' for local ollama)",
    )

    # HTTP client
    max_concurrent_requests: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max parallel HTTP requests",
    )
    request_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Request timeout in seconds",
    )
    retry_attempts: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of retry attempts on failure",
    )
    retry_wait_seconds: float = Field(
        default=1.0,
        description="Base wait time between retries (exponential backoff)",
    )
    rate_limit_rps: float = Field(
        default=20.0,
        description="Max requests per second to the target",
    )

    # Proxy
    http_proxy: str | None = Field(
        default=None,
        description="HTTP proxy URL (e.g. http://127.0.0.1:8080)",
    )

    # Output
    output_dir: str = Field(
        default="./reports",
        description="Directory for generated reports",
    )

    # Scan behavior
    verify_findings: bool = Field(
        default=True,
        description="Re-test findings to reduce false positives",
    )
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to include a finding in the report",
    )
    enable_llm_analysis: bool = Field(
        default=True,
        description="Use LLM for deeper analysis (disable for fast mode)",
    )
    enable_llm_cache: bool = Field(
        default=True,
        description="Cache LLM responses to avoid duplicate calls",
    )

    # Test users — can be overridden via env
    test_users: Dict[str, Any] = Field(
        default={
            "admin": {
                "email": "admin@vulnshop.com",
                "password": "admin123",
                "role": "admin",
            },
            "seller": {
                "email": "seller1@vulnshop.com",
                "password": "password123",
                "role": "seller",
            },
            "customer1": {
                "email": "customer1@vulnshop.com",
                "password": "password123",
                "role": "customer",
            },
            "customer2": {
                "email": "customer2@vulnshop.com",
                "password": "password123",
                "role": "customer",
            },
        },
        description="Test user credentials keyed by alias",
    )

    @field_validator("target_url", "llm_base_url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

    @property
    def auth_endpoint(self) -> str:
        return f"{self.target_url}/auth/login"


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
