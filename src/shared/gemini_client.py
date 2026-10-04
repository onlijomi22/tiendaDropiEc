"""DEPRECATED: Use src.infrastructure.ai.gemini_adapter.GeminiAdapter instead.

This module exists only for backward compatibility during migration.
"""

import warnings
from src.infrastructure.ai.gemini_adapter import GeminiAdapter

_adapter = None


def get_gemini_model():
    """DEPRECATED: Use GeminiAdapter instead."""
    warnings.warn(
        "get_gemini_model() is deprecated. Use GeminiAdapter from "
        "src.infrastructure.ai.gemini_adapter instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    global _adapter
    if _adapter is None:
        _adapter = GeminiAdapter()
    return _adapter
