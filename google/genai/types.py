"""Simple types used by the local Runner stub and `run_agent`.

Only implements the small surface the project expects: `Part` and
`Content` with `text`/`parts` attributes.
"""

from typing import List

class Part:
    def __init__(self, text: str = ""):
        self.text = text

class Content:
    def __init__(self, role: str = "user", parts: List[Part] = None):
        self.role = role
        self.parts = parts or []

__all__ = ["Part", "Content"]
