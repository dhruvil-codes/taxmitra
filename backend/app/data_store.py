"""Cached loaders for the synthetic data files."""

from __future__ import annotations

import json
import os
from functools import lru_cache

from app.config import get_settings


@lru_cache(maxsize=1)
def _read(file_name: str) -> list | dict:
    path = os.path.join(get_settings().data_dir, file_name)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_citizens() -> list[dict]:
    return _read("citizens.json")


def load_notices() -> list[dict]:
    return _read("notices.json")


def get_notice(notice_id: str) -> dict | None:
    return next((n for n in load_notices() if n["id"] == notice_id), None)


def get_citizen(citizen_id: str) -> dict | None:
    return next((c for c in load_citizens() if c["id"] == citizen_id), None)


def load_draft_templates() -> dict[str, str]:
    return _read("draft_templates.json")
