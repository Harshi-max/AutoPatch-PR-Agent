"""Minimal local stub of google.genai used for development/testing.

This provides a tiny `types` and `agents` surface so the repository can
run without the real Google GenAI SDK installed. It is intentionally
minimal and synchronous behavior is simulated for demo purposes.
"""

from . import agents as agents
from . import types as types

__all__ = ["agents", "types"]
