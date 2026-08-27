"""Ephemeral extraction sessions; uploaded bytes are never retained."""
from __future__ import annotations
import hashlib
import secrets
import time

_SESSIONS: dict[str, tuple[float, dict]] = {}
TTL_SECONDS = 30 * 60

def create_session(payload: dict) -> tuple[str, str]:
    session_id = secrets.token_urlsafe(24)
    fingerprint = hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()
    _SESSIONS[session_id] = (time.time(), {**payload, "fingerprint": fingerprint, "confirmed": False})
    return session_id, fingerprint

def get_session(session_id: str) -> dict | None:
    value = _SESSIONS.get(session_id)
    if not value:
        return None
    created, payload = value
    if time.time() - created > TTL_SECONDS:
        _SESSIONS.pop(session_id, None)
        return None
    return payload

def confirm_session(session_id: str, fingerprint: str) -> dict | None:
    payload = get_session(session_id)
    if payload is None or not secrets.compare_digest(payload["fingerprint"], fingerprint):
        return None
    payload["confirmed"] = True
    return payload
