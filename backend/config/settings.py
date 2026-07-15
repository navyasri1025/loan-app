"""
config/settings.py — Centralised application configuration.

All values are read from environment variables / .env file.
No secrets are hardcoded here.

Required:
    OPENROUTER_API_KEY   — your OpenRouter key (sk-or-...)
    OPENROUTER_MODEL     — model slug, e.g. deepseek/deepseek-chat-v3-0324

Optional (have sensible defaults):
    OPENROUTER_BASE_URL
    OPENROUTER_TIMEOUT
    OPENROUTER_MAX_RETRIES
    OPENROUTER_SITE_URL / OPENROUTER_SITE_NAME   — shown in OpenRouter dashboard
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application-wide settings, sourced from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # ignore unknown env vars silently
    )

    # ── OpenRouter (required) ────────────────────────────────────────────────
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key (sk-or-...). REQUIRED.",
    )
    openrouter_model: str = Field(
        default="deepseek/deepseek-chat-v3-0324",
        description="OpenRouter model slug.",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter OpenAI-compatible base URL.",
    )

    # ── HTTP settings ────────────────────────────────────────────────────────
    openrouter_timeout: float = Field(
        default=60.0,
        description="Per-request timeout in seconds.",
    )
    openrouter_max_retries: int = Field(
        default=3,
        description="Max retries for 429 / 5xx responses.",
    )
    openrouter_retry_base_delay: float = Field(
        default=1.0,
        description="Base backoff delay in seconds (doubles each retry).",
    )

    # ── HTTP Referer headers (optional, shown in OpenRouter dashboard) ────────
    openrouter_site_url: str = Field(
        default="http://localhost:8000",
        description="Your site URL, sent as HTTP-Referer.",
    )
    openrouter_site_name: str = Field(
        default="Apex Credit Loan Processing Agent",
        description="Your app name, sent as X-Title.",
    )

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/loan_db",
    )
    use_sqlite: bool = Field(default=False)

    # ── Security ─────────────────────────────────────────────────────────────
    jwt_secret: str = Field(
        default="supersecretjwtsecretkeychangeinproduction1234567890!",
    )
    access_token_expire_minutes: int = Field(default=60)

    # ── App ──────────────────────────────────────────────────────────────────
    environment: str = Field(default="development")
    port: int = Field(default=8000)

    # ── Validation ───────────────────────────────────────────────────────────
    @field_validator("openrouter_api_key")
    @classmethod
    def key_must_not_be_placeholder(cls, v: str) -> str:
        placeholders = {"", "mock-key-for-local-testing", "your-key-here", "sk-or-xxx"}
        if v.lower() in placeholders:
            return ""          # Return empty; startup check will handle it
        return v

    @property
    def is_openrouter_configured(self) -> bool:
        """True when a real (non-empty) key is present."""
        return bool(self.openrouter_api_key)

    @property
    def openrouter_headers(self) -> dict:
        """
        Standard headers to attach to every OpenRouter request.
        The key is NOT logged or returned to clients — it lives only here.
        """
        return {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": self.openrouter_site_url,
            "X-Title": self.openrouter_site_name,
            "Content-Type": "application/json",
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the singleton Settings instance.
    Uses lru_cache so the .env file is parsed only once.
    """
    return Settings()
