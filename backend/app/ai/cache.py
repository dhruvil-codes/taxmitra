"""Content store: pre-generated static fallbacks first, live AI last.

DEMO_MODE=true means the store never touches the network — every request
is served from files committed to the repo. That is what makes judging
traffic free and the demo unbreakable.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class ServedContent:
    content: dict
    source: str  # "static" | "cache" | "live"
    degraded: bool  # True when we wanted live AI but could not use it


class ContentStore:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._static: dict[str, dict] = {}
        self._memory: dict[str, dict] = {}
        for name in os.listdir(settings.static_fallbacks_dir):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(settings.static_fallbacks_dir, name), encoding="utf-8") as fh:
                payload = json.load(fh)
            key = name[: -len(".json")]
            self._static[key] = payload

    def get_static(self, key: str) -> dict | None:
        return self._static.get(key)

    def put_memory(self, key: str, content: dict) -> None:
        self._memory[key] = content

    def get_memory(self, key: str) -> dict | None:
        return self._memory.get(key)

    def live_allowed(self) -> bool:
        """Live AI is used only outside DEMO_MODE and only with a key."""
        return not self._settings.demo_mode and bool(self._settings.openai_api_key)


_store: ContentStore | None = None


def get_store() -> ContentStore:
    global _store  # noqa: PLW0603
    if _store is None:
        from app.config import get_settings

        _store = ContentStore(get_settings())
    return _store


def reset_store() -> None:
    """Test helper: rebuild the store after settings change."""
    global _store  # noqa: PLW0603
    _store = None
