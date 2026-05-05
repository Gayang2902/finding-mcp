"""
Unit tests for LLMClient.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.utils.llm_client import LLMClient


def _make_client(**kwargs) -> LLMClient:
    return LLMClient(
        base_url="http://localhost:11434/v1",
        model="llama3:8b",
        api_key="ollama",
        enable_cache=kwargs.get("enable_cache", True),
        max_retries=kwargs.get("max_retries", 1),
    )


def _mock_completion(text: str) -> MagicMock:
    """Build a mock OpenAI completion object."""
    choice = MagicMock()
    choice.message.content = text
    usage = MagicMock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 20
    usage.total_tokens = 30
    completion = MagicMock()
    completion.choices = [choice]
    completion.usage = usage
    return completion


class TestLLMClientAnalyze:

    @pytest.mark.asyncio
    async def test_returns_text_response(self) -> None:
        """analyze() returns the LLM text."""
        client = _make_client()
        mock_completion = _mock_completion("Hello from LLM")

        with patch.object(client._client.chat.completions, "create", new=AsyncMock(return_value=mock_completion)):
            result = await client.analyze("Test prompt")

        assert result == "Hello from LLM"

    @pytest.mark.asyncio
    async def test_cache_hit_skips_llm_call(self) -> None:
        """Second identical request uses cached response."""
        client = _make_client(enable_cache=True)
        mock_completion = _mock_completion("Cached response")

        with patch.object(client._client.chat.completions, "create", new=AsyncMock(return_value=mock_completion)) as mock_create:
            await client.analyze("Same prompt")
            await client.analyze("Same prompt")  # should hit cache

        mock_create.assert_called_once()  # only one real LLM call

    @pytest.mark.asyncio
    async def test_cache_disabled_always_calls_llm(self) -> None:
        """With cache disabled, every call goes to LLM."""
        client = _make_client(enable_cache=False)
        mock_completion = _mock_completion("Fresh response")

        with patch.object(client._client.chat.completions, "create", new=AsyncMock(return_value=mock_completion)) as mock_create:
            await client.analyze("Same prompt")
            await client.analyze("Same prompt")

        assert mock_create.call_count == 2

    @pytest.mark.asyncio
    async def test_different_prompts_not_cached(self) -> None:
        """Different prompts produce separate LLM calls."""
        client = _make_client()
        mock_completion = _mock_completion("Response")

        with patch.object(client._client.chat.completions, "create", new=AsyncMock(return_value=mock_completion)) as mock_create:
            await client.analyze("Prompt A")
            await client.analyze("Prompt B")

        assert mock_create.call_count == 2


class TestJSONExtraction:

    def test_parses_raw_json(self) -> None:
        result = LLMClient._extract_json('{"key": "value", "num": 42}')
        assert result == {"key": "value", "num": 42}

    def test_extracts_json_from_markdown_fence(self) -> None:
        text = "Here is the result:\n```json\n{\"is_idor\": true}\n```"
        result = LLMClient._extract_json(text)
        assert result == {"is_idor": True}

    def test_extracts_json_from_plain_fence(self) -> None:
        text = "```\n{\"confidence\": 0.9}\n```"
        result = LLMClient._extract_json(text)
        assert result == {"confidence": 0.9}

    def test_extracts_json_embedded_in_text(self) -> None:
        text = 'Analysis: {"severity": "HIGH", "confidence": 0.8} — end of analysis.'
        result = LLMClient._extract_json(text)
        assert result.get("severity") == "HIGH"

    def test_returns_error_dict_on_failure(self) -> None:
        result = LLMClient._extract_json("This is not JSON at all.")
        assert "error" in result
        assert result["error"] == "json_parse_failed"

    def test_handles_nested_json(self) -> None:
        nested = {"outer": {"inner": [1, 2, 3]}, "flag": True}
        result = LLMClient._extract_json(json.dumps(nested))
        assert result == nested

    def test_handles_list_response(self) -> None:
        result = LLMClient._extract_json('[{"id": 1}, {"id": 2}]')
        assert isinstance(result, list)
        assert len(result) == 2


class TestAnalyzeJSON:

    @pytest.mark.asyncio
    async def test_analyze_json_parses_response(self) -> None:
        client = _make_client()
        mock_completion = _mock_completion('{"is_vulnerable": true, "confidence": 0.85}')

        with patch.object(client._client.chat.completions, "create", new=AsyncMock(return_value=mock_completion)):
            result = await client.analyze_json("Analyze this endpoint")

        assert result.get("is_vulnerable") is True
        assert result.get("confidence") == 0.85

    @pytest.mark.asyncio
    async def test_analyze_json_handles_markdown_wrapped_response(self) -> None:
        client = _make_client()
        wrapped = '```json\n{"severity": "CRITICAL"}\n```'
        mock_completion = _mock_completion(wrapped)

        with patch.object(client._client.chat.completions, "create", new=AsyncMock(return_value=mock_completion)):
            result = await client.analyze_json("Analyze")

        assert result.get("severity") == "CRITICAL"


class TestStats:

    @pytest.mark.asyncio
    async def test_stats_track_calls(self) -> None:
        client = _make_client(enable_cache=False)
        mock_completion = _mock_completion("OK")

        with patch.object(client._client.chat.completions, "create", new=AsyncMock(return_value=mock_completion)):
            await client.analyze("P1")
            await client.analyze("P2")

        assert client.stats["calls"] == 2

    def test_clear_cache(self) -> None:
        client = _make_client()
        client._cache["key"] = "value"
        client.clear_cache()
        assert len(client._cache) == 0
