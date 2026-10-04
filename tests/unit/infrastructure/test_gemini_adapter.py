"""Unit tests for GeminiAdapter."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.infrastructure.ai.gemini_adapter import GeminiAdapter, GeminiChatResponse


class TestGeminiAdapterExtractJson:
    """Test JSON extraction from text responses."""

    def test_extracts_valid_json(self):
        text = 'Here is the result: {"name": "test", "price": 25.0} end.'
        result = GeminiAdapter._extract_json(text)
        assert result == {"name": "test", "price": 25.0}

    def test_returns_empty_on_no_json(self):
        result = GeminiAdapter._extract_json("No JSON here at all")
        assert result == {}

    def test_returns_empty_on_invalid_json(self):
        result = GeminiAdapter._extract_json("Here: {invalid json content}")
        assert result == {}

    def test_extracts_nested_json(self):
        text = '{"outer": {"inner": [1, 2, 3]}, "key": "value"}'
        result = GeminiAdapter._extract_json(text)
        assert result["outer"]["inner"] == [1, 2, 3]


class TestGeminiChatResponse:
    """Test chat response parsing."""

    def test_text_response(self):
        mock_resp = MagicMock()
        mock_resp.text = "Hello world"
        response = GeminiChatResponse(mock_resp)
        assert response.text == "Hello world"
        assert response.has_tool_call is False
        assert response.tool_call is None

    def test_tool_call_response(self):
        mock_fc = MagicMock()
        mock_fc.name = "search_products"
        mock_fc.args = {"category": "cocina", "limit": 10}

        mock_part = MagicMock()
        mock_part.function_call = mock_fc

        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]

        mock_resp = MagicMock()
        mock_resp.candidates = [mock_candidate]
        mock_resp.text = None  # Tool calls don't have text

        response = GeminiChatResponse(mock_resp)
        assert response.has_tool_call is True
        name, args = response.tool_call
        assert name == "search_products"
        assert args["category"] == "cocina"

    def test_empty_response(self):
        mock_resp = MagicMock()
        mock_resp.text = None
        mock_resp.candidates = []
        response = GeminiChatResponse(mock_resp)
        assert response.text is None
        assert response.has_tool_call is False
