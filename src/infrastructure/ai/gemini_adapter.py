"""Gemini AI adapter — single point of access for all Gemini interactions.

Wraps the google.genai SDK (new) and provides domain-oriented methods.
No other module should import google.genai directly.

Usage:
    adapter = GeminiAdapter()
    text = await adapter.generate("Describe this product")
    data = await adapter.generate_json("Return JSON with keys: name, price")
    chat = adapter.create_chat(tools=[...])
"""

from __future__ import annotations

import asyncio
import json
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types

from src.shared.config import get_gemini_settings
from src.shared.logger import logger


class GeminiAdapter:
    """Unified adapter for Google Gemini API.

    Centralizes client initialization, model selection, and error handling.
    All Gemini interactions in the project go through this adapter.
    """

    def __init__(self, model: str | None = None) -> None:
        settings = get_gemini_settings()
        self._client = genai.Client(api_key=settings.api_key.get_secret_value())
        self._model = model or settings.model

    @property
    def client(self) -> genai.Client:
        """Direct access to the underlying client (for advanced use cases)."""
        return self._client

    @property
    def model(self) -> str:
        return self._model

    async def generate(self, prompt: str, *, model: str | None = None) -> str:
        """Generate text from a prompt.

        Args:
            prompt: The input prompt.
            model: Optional model override.

        Returns:
            Generated text string.
        """
        target_model = model or self._model
        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=target_model,
            contents=prompt,
        )
        return response.text

    async def generate_json(self, prompt: str, *, model: str | None = None) -> dict:
        """Generate content and parse JSON from the response.

        Extracts the first JSON object found in the response text.

        Args:
            prompt: The input prompt (should request JSON output).
            model: Optional model override.

        Returns:
            Parsed dict, or empty dict if parsing fails.
        """
        text = await self.generate(prompt, model=model)
        return self._extract_json(text)

    async def generate_with_search(
        self, prompt: str, *, model: str | None = None
    ) -> str:
        """Generate content with Google Search grounding enabled.

        Gemini will search the web before responding, providing
        real data rather than hallucinated content.

        Args:
            prompt: The input prompt.
            model: Optional model override.

        Returns:
            Generated text with real web data.
        """
        target_model = model or self._model
        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=target_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        return response.text

    async def generate_json_with_search(
        self, prompt: str, *, model: str | None = None
    ) -> dict:
        """Generate with search grounding and parse JSON from response.

        Args:
            prompt: The input prompt (should request JSON output).
            model: Optional model override.

        Returns:
            Parsed dict, or empty dict if parsing fails.
        """
        text = await self.generate_with_search(prompt, model=model)
        return self._extract_json(text)

    def create_chat(
        self,
        *,
        tools: list[types.Tool] | None = None,
        model: str | None = None,
        system_instruction: str | None = None,
    ) -> "GeminiChat":
        """Create a chat session for multi-turn conversations (e.g., ReAct agents).

        Args:
            tools: Function declarations for tool calling.
            model: Optional model override.
            system_instruction: System prompt for the chat.

        Returns:
            GeminiChat wrapper for send/receive with tool calling.
        """
        target_model = model or self._model
        config: dict[str, Any] = {}
        if tools:
            config["tools"] = tools
        if system_instruction:
            config["system_instruction"] = system_instruction

        chat = self._client.chats.create(
            model=target_model,
            config=types.GenerateContentConfig(**config) if config else None,
        )
        return GeminiChat(chat)

    def build_function_tool(self, callables: list) -> list[types.Tool]:
        """Build Tool definitions from Python callables for function calling.

        Uses Gemini's automatic function signature extraction.

        Args:
            callables: List of Python functions to expose as tools.

        Returns:
            List of Tool objects ready for create_chat().
        """
        declarations = []
        for fn in callables:
            declarations.append(
                types.FunctionDeclaration.from_callable(callable=fn, client=self._client)
            )
        return [types.Tool(function_declarations=declarations)]

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract the first JSON object from text."""
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.warning("[GeminiAdapter] Failed to parse JSON from response")
        return {}


class GeminiChat:
    """Wrapper around a Gemini chat session for the ReAct loop.

    Provides sync-friendly send that handles tool call detection.
    """

    def __init__(self, chat: Any) -> None:
        self._chat = chat

    async def send(self, message: str) -> "GeminiChatResponse":
        """Send a message and return a parsed response.

        Args:
            message: Text message to send.

        Returns:
            GeminiChatResponse with text or tool call info.
        """
        response = await asyncio.to_thread(
            self._chat.send_message, message
        )
        return GeminiChatResponse(response)


class GeminiChatResponse:
    """Parsed response from a Gemini chat turn."""

    def __init__(self, response: Any) -> None:
        self._response = response

    @property
    def text(self) -> str | None:
        """Return text if this is a text response, else None."""
        try:
            return self._response.text
        except (AttributeError, ValueError):
            return None

    @property
    def has_tool_call(self) -> bool:
        """Check if response contains a function call."""
        try:
            parts = self._response.candidates[0].content.parts
            return any(
                hasattr(p, "function_call") and p.function_call and p.function_call.name
                for p in parts
            )
        except (AttributeError, IndexError):
            return False

    @property
    def tool_call(self) -> tuple[str, dict] | None:
        """Extract tool name and args from function call.

        Returns:
            Tuple of (tool_name, args_dict) or None.
        """
        try:
            parts = self._response.candidates[0].content.parts
            for p in parts:
                if hasattr(p, "function_call") and p.function_call and p.function_call.name:
                    return (p.function_call.name, dict(p.function_call.args))
        except (AttributeError, IndexError):
            pass
        return None
