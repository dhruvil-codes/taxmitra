"""DEMO_MODE must guarantee: zero live AI calls, full journey still works.

The provider is monkeypatched to explode — if any code path tries to reach
OpenAI during these tests, they fail loudly. This is the kill-the-key drill.
"""

from fastapi.testclient import TestClient

from app.ai import provider as provider_module
from app.main import app

client = TestClient(app)


class _ExplodingProvider:
    def chat_json(self, *args, **kwargs):
        raise AssertionError("DEMO_MODE must never trigger a live AI call")


def test_explanation_never_touches_live_ai_in_demo_mode(monkeypatch):
    monkeypatch.setattr(provider_module, "ChatProvider", _ExplodingProvider)
    body = client.get("/api/ai/explanation/N-2026-001", params={"locale": "en"}).json()
    assert body["source"] == "static"
    assert body["content"]["plain_language"]


def test_kill_the_key_drill_hi():
    # No API key is configured in tests; the journey must not care in DEMO_MODE.
    body = client.get("/api/ai/explanation/N-2026-001", params={"locale": "hi"}).json()
    assert "₹45,000" in body["content"]["plain_language"]
    assert body["citations"]


def test_full_journey_completes_without_live_ai(monkeypatch):
    monkeypatch.setattr(provider_module, "ChatProvider", _ExplodingProvider)
    answers = {"q1_received": "yes", "q2_in_return": "no", "q3_documents": "unsure"}
    body = client.post("/api/workflow/resolve", json={"notice_id": "N-2026-001", "answers": answers}).json()
    assert body["supported"] is True
    assert body["path"]["path_id"] == "agree_report_now"
    assert body["checklist"][0]["id"] == "doc_ais_download"
    assert body["draft"]
