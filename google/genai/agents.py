"""Minimal Runner and session service stub for development/testing.

The `Runner` implements an `stream_input_content` async generator that
yields a single event echoing the user's prompt back. This is sufficient
for the repository's local flows and avoids requiring the real SDK.
"""

import asyncio
from typing import AsyncGenerator

from .types import Content, Part

class _Delta:
    def __init__(self, parts):
        self.parts = parts

class _Event:
    def __init__(self, type_, delta):
        self.type = type_
        self.delta = delta

class InMemorySessionService:
    def __init__(self):
        self._sessions = {}

class Runner:
    def __init__(self, model: str = None, app: str = None, session_service=None):
        self.model = model
        self.app = app
        self.session_service = session_service

    async def stream_input_content(self, session_id: str, content: Content) -> AsyncGenerator[_Event, None]:
        # Simulate asynchronous streaming by yielding the prompt text as one event
        await asyncio.sleep(0)  # yield control
        text = ""
        for part in getattr(content, "parts", []) or []:
            if getattr(part, "text", None):
                text += part.text

        part_obj = Part(text=text)
        delta = _Delta(parts=[part_obj])
        event = _Event(type_="response.delta", delta=delta)
        yield event

__all__ = ["Runner", "InMemorySessionService"]
