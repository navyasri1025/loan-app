"""
app/core/openrouter_client.py — Single reusable OpenRouter LLM client.

Features
--------
* OpenAI-compatible endpoint (https://openrouter.ai/api/v1/chat/completions)
* Reads all config from config.settings — never hardcodes keys or models
* Retry logic for HTTP 429 / 500 / 502 / 503 with exponential back-off
* Configurable timeout per request
* Structured logging: request_id, model, prompt_tokens, completion_tokens,
  latency_ms, error — API key is NEVER logged
* Clear errors when key is missing or invalid — app does NOT crash
* Thread-safe singleton via module-level instance

Usage
-----
    from app.core.openrouter_client import openrouter_client

    response = await openrouter_client.chat(
        system="You are a credit analyst.",
        user="Evaluate this applicant...",
        temperature=0.2,
    )
    # response is a plain string (the assistant's reply)
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Optional

import httpx

from app.core.logging import get_logger
from config.settings import get_settings

logger = get_logger("core.openrouter_client")

# Retry-able HTTP status codes
_RETRYABLE = {429, 500, 502, 503}


class OpenRouterError(Exception):
    """Raised when the OpenRouter API returns an unrecoverable error."""


class OpenRouterKeyMissingError(OpenRouterError):
    """Raised when no API key is configured."""


class OpenRouterInvalidKeyError(OpenRouterError):
    """Raised when the key is present but rejected by OpenRouter (401/403)."""


class OpenRouterClient:
    """
    Reusable async client for OpenRouter's OpenAI-compatible chat endpoint.

    Do NOT instantiate this yourself — use the module-level singleton
    ``openrouter_client``.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    async def chat(
        self,
        user: str,
        system: Optional[str] = None,
        *,
        temperature: float = 0.3,
        max_tokens: int = 1500,
        json_mode: bool = False,
    ) -> str:
        """
        Send a chat completion request and return the assistant's reply as a
        plain string.

        Parameters
        ----------
        user:        The user / human turn message.
        system:      Optional system prompt.
        temperature: Sampling temperature (0 = deterministic).
        max_tokens:  Maximum tokens to generate.
        json_mode:   If True, instructs the model to reply with valid JSON.

        Raises
        ------
        OpenRouterKeyMissingError   — OPENROUTER_API_KEY is not set.
        OpenRouterInvalidKeyError   — API returned 401 / 403.
        OpenRouterError             — Any other non-retryable error.
        """
        self._assert_key_configured()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        payload: dict = {
            "model": self._settings.openrouter_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        return await self._post_with_retry(payload)

    async def complete(self, prompt: str, **kwargs) -> str:
        """Convenience wrapper — treats the entire prompt as the user turn."""
        return await self.chat(user=prompt, **kwargs)

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _assert_key_configured(self) -> None:
        """Raise immediately if no API key is configured."""
        if not self._settings.is_openrouter_configured:
            raise OpenRouterKeyMissingError(
                "OpenRouter API key not found. "
                "Please configure OPENROUTER_API_KEY in your .env file."
            )

    async def _post_with_retry(self, payload: dict) -> str:
        """
        POST to the completions endpoint with exponential-backoff retry.
        Logs request_id, model, tokens, latency, and errors — never the key.
        """
        request_id = str(uuid.uuid4())[:8]
        url = f"{self._settings.openrouter_base_url}/chat/completions"
        max_retries = self._settings.openrouter_max_retries
        base_delay = self._settings.openrouter_retry_base_delay
        timeout = self._settings.openrouter_timeout

        attempt = 0
        last_error: Optional[Exception] = None

        while attempt <= max_retries:
            t0 = time.monotonic()
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(timeout)
                ) as client:
                    resp = await client.post(
                        url,
                        headers=self._settings.openrouter_headers,
                        json=payload,
                    )

                latency_ms = int((time.monotonic() - t0) * 1000)

                # ── Auth errors (never retry) ─────────────────────────────
                if resp.status_code in (401, 403):
                    logger.error(
                        "OpenRouter auth failure",
                        extra={
                            "request_id": request_id,
                            "status": resp.status_code,
                            "latency_ms": latency_ms,
                            "model": self._settings.openrouter_model,
                        },
                    )
                    raise OpenRouterInvalidKeyError(
                        "OpenRouter API key is invalid or lacks permissions. "
                        "Please check OPENROUTER_API_KEY."
                    )

                # ── Retryable errors ──────────────────────────────────────
                if resp.status_code in _RETRYABLE:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        "OpenRouter retryable error — will retry",
                        extra={
                            "request_id": request_id,
                            "status": resp.status_code,
                            "attempt": attempt + 1,
                            "retry_in_s": delay,
                            "model": self._settings.openrouter_model,
                        },
                    )
                    last_error = OpenRouterError(
                        f"HTTP {resp.status_code} from OpenRouter"
                    )
                    attempt += 1
                    await asyncio.sleep(delay)
                    continue

                # ── Other non-200 ─────────────────────────────────────────
                if resp.status_code != 200:
                    body = resp.text[:300]
                    logger.error(
                        "OpenRouter unexpected error",
                        extra={
                            "request_id": request_id,
                            "status": resp.status_code,
                            "body_preview": body,
                            "model": self._settings.openrouter_model,
                        },
                    )
                    raise OpenRouterError(
                        f"OpenRouter returned HTTP {resp.status_code}. "
                        "Check the application logs for details."
                    )

                # ── Success ───────────────────────────────────────────────
                data = resp.json()
                usage = data.get("usage", {})
                content = (
                    data["choices"][0]["message"]["content"]
                    if data.get("choices")
                    else ""
                )

                logger.info(
                    "OpenRouter request completed",
                    extra={
                        "request_id": request_id,
                        "model": self._settings.openrouter_model,
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                        "latency_ms": latency_ms,
                        "attempt": attempt + 1,
                    },
                )

                return content

            except (OpenRouterError, OpenRouterKeyMissingError, OpenRouterInvalidKeyError):
                raise  # propagate without retry

            except httpx.TimeoutException:
                latency_ms = int((time.monotonic() - t0) * 1000)
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "OpenRouter request timed out — retrying",
                    extra={
                        "request_id": request_id,
                        "latency_ms": latency_ms,
                        "attempt": attempt + 1,
                        "retry_in_s": delay,
                        "model": self._settings.openrouter_model,
                    },
                )
                last_error = OpenRouterError(
                    f"Request timed out after {timeout}s"
                )
                attempt += 1
                await asyncio.sleep(delay)

            except Exception as exc:
                latency_ms = int((time.monotonic() - t0) * 1000)
                logger.error(
                    "Unexpected error calling OpenRouter",
                    extra={
                        "request_id": request_id,
                        "error_type": type(exc).__name__,
                        "latency_ms": latency_ms,
                        "model": self._settings.openrouter_model,
                    },
                    exc_info=True,
                )
                raise OpenRouterError(
                    f"Unexpected error: {type(exc).__name__}. "
                    "See application logs for details."
                ) from exc

        # All retries exhausted
        raise last_error or OpenRouterError("All retry attempts exhausted.")

    # ──────────────────────────────────────────────────────────────────────────
    # JSON helper
    # ──────────────────────────────────────────────────────────────────────────

    async def chat_json(
        self,
        user: str,
        system: Optional[str] = None,
        *,
        temperature: float = 0.1,
        max_tokens: int = 1500,
    ) -> dict:
        """
        Like ``chat()``, but parses and returns the response as a dict.
        Instructs the model to return valid JSON.
        Falls back gracefully if the model returns non-JSON.
        """
        raw = await self.chat(
            user=user,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Extract first {...} block from the response
            import re
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except json.JSONDecodeError:
                    pass
            logger.warning(
                "OpenRouter returned non-JSON despite json_mode=True; "
                "returning raw text under 'raw' key."
            )
            return {"raw": raw}


# ── Module-level singleton ────────────────────────────────────────────────────
# Import this everywhere instead of instantiating OpenRouterClient directly.
openrouter_client = OpenRouterClient()
