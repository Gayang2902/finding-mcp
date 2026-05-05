"""
LLM client using OpenAI-compatible API (works with ollama, vllm, lm-studio).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)

_SENTINEL = object()


class LLMClient:
    """
    Async LLM client with:
    - OpenAI-compatible API support
    - JSON extraction from markdown code blocks
    - Response caching (in-memory, keyed by prompt hash)
    - Retry on transient errors
    - Token usage tracking
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "ollama",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        enable_cache: bool = True,
        max_retries: int = 3,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_cache = enable_cache
        self.max_retries = max_retries

        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            max_retries=0,  # we handle retries ourselves
        )
        self._cache: Dict[str, str] = {}
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._call_count = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a prompt to the LLM and return the raw text response.

        Args:
            prompt: User message
            system_prompt: Optional system instruction
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Returns:
            LLM response text
        """
        cache_key = self._cache_key(prompt, system_prompt or "")
        if self.enable_cache and cache_key in self._cache:
            logger.debug("LLM cache hit for prompt hash %s", cache_key[:8])
            return self._cache[cache_key]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response_text = await self._call_with_retry(
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
        )

        if self.enable_cache:
            self._cache[cache_key] = response_text

        return response_text

    async def analyze_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a prompt expecting a JSON response. Extracts JSON from markdown
        code blocks if the model wraps its output.

        Returns:
            Parsed dict, or {"error": "...", "raw": "..."} on parse failure.
        """
        json_hint = "\n\nRespond ONLY with valid JSON. No additional text."
        raw = await self.analyze(prompt + json_hint, system_prompt=system_prompt)
        return self._extract_json(raw)

    async def batch_analyze(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
    ) -> List[str]:
        """
        Analyze multiple prompts sequentially (local LLMs typically can't parallelize).
        """
        results = []
        for prompt in prompts:
            result = await self.analyze(prompt, system_prompt=system_prompt)
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _call_with_retry(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 2):
            try:
                t0 = time.monotonic()
                completion = await self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                elapsed = time.monotonic() - t0
                self._call_count += 1

                if completion.usage:
                    self._total_prompt_tokens += completion.usage.prompt_tokens or 0
                    self._total_completion_tokens += completion.usage.completion_tokens or 0

                text = completion.choices[0].message.content or ""
                logger.debug("LLM call #%d: %.1fs, %d tokens", self._call_count, elapsed,
                             (completion.usage.total_tokens if completion.usage else 0))
                return text

            except (APIConnectionError, RateLimitError) as exc:
                last_exc = exc
                if attempt <= self.max_retries:
                    wait = 2 ** (attempt - 1)
                    logger.warning("LLM error (attempt %d): %s — retrying in %ds", attempt, exc, wait)
                    import asyncio
                    await asyncio.sleep(wait)
            except APIError as exc:
                logger.error("LLM API error: %s", exc)
                raise

        raise RuntimeError(f"LLM call failed after {self.max_retries + 1} attempts") from last_exc

    @staticmethod
    def _cache_key(prompt: str, system_prompt: str) -> str:
        content = f"{system_prompt}|{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """
        Extract the first JSON object or array from *text*.
        Handles markdown code blocks (```json ... ```).
        """
        # Strip markdown code fences
        fence = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
        if fence:
            text = fence.group(1).strip()

        # Try to parse directly
        try:
            return json.loads(text)  # type: ignore[return-value]
        except json.JSONDecodeError:
            pass

        # Find first {...} or [...] block
        for pattern in (r"\{[\s\S]+\}", r"\[[\s\S]+\]"):
            match = re.search(pattern, text)
            if match:
                try:
                    return json.loads(match.group())  # type: ignore[return-value]
                except json.JSONDecodeError:
                    pass

        logger.warning("Failed to extract JSON from LLM response: %s", text[:200])
        return {"error": "json_parse_failed", "raw": text}

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    @property
    def stats(self) -> Dict[str, int]:
        return {
            "calls": self._call_count,
            "cache_size": len(self._cache),
            "prompt_tokens": self._total_prompt_tokens,
            "completion_tokens": self._total_completion_tokens,
            "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
        }

    def clear_cache(self) -> None:
        self._cache.clear()
