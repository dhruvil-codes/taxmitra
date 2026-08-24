from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True  # conftest forces DEMO_MODE
    assert body["chat_model"] == get_settings().openai_chat_model


def test_citizens():
    body = client.get("/api/citizens").json()
    assert len(body) == 1
    assert body[0]["id"] == "C-001"


def test_notices_list_includes_computed_deadline():
    body = client.get("/api/notices", params={"citizen_id": "C-001"}).json()
    by_id = {n["id"]: n for n in body}
    hero = by_id["N-2026-001"]
    assert hero["supported"] is True
    assert hero["due_date"] == "2026-09-12"
    assert hero["amount_in_question"] == 45000
    assert by_id["N-2026-002"]["supported"] is False


def test_notice_detail_contains_official_text():
    body = client.get("/api/notices/N-2026-001").json()
    assert "143(1)(a)" in body["official_text"]
    assert body["status"] in ("action_required", "due_soon", "expired")


def test_questions_render_notice_amount():
    body = client.get("/api/workflow/questions/N-2026-001", params={"locale": "en"}).json()
    assert len(body["questions"]) == 3
    assert "₹45,000" in body["questions"][0]["text"]
    hi = client.get("/api/workflow/questions/N-2026-001", params={"locale": "hi"}).json()
    assert "₹45,000" in hi["questions"][0]["text"]
    assert hi["questions"][0]["text"] != body["questions"][0]["text"]


def test_resolve_happy_path_disagree_already_reported():
    payload = {
        "notice_id": "N-2026-001",
        "answers": {"q1_received": "yes", "q2_in_return": "yes", "q3_documents": "yes"},
    }
    body = client.post("/api/workflow/resolve", json=payload).json()
    assert body["supported"] is True
    assert body["path"]["path_id"] == "disagree_already_reported"
    assert body["path"]["position"] == "disagree"
    assert body["checklist"][0]["id"] == "doc_itr_extract"
    assert body["deadline"]["due_date"] == "2026-09-12"
    assert "₹45,000" in body["draft"]
    assert body["official_step"]["url"].startswith("https://www.incometax.gov.in")
    assert "has not submitted" in body["official_step"]["boundary"]["en"]


def test_resolve_missing_answers_is_422():
    payload = {"notice_id": "N-2026-001", "answers": {"q1_received": "yes"}}
    assert client.post("/api/workflow/resolve", json=payload).status_code == 422


def test_resolve_unsupported_notice_returns_refusal():
    payload = {
        "notice_id": "N-2026-002",
        "answers": {"q1_received": "yes", "q2_in_return": "yes", "q3_documents": "yes"},
    }
    body = client.post("/api/workflow/resolve", json=payload).json()
    assert body["supported"] is False
    assert body["headline"]["en"].startswith("We can't safely guide you")
    assert any("incometax.gov.in" in link["url"] for link in body["official_links"])


def test_refusal_endpoint():
    body = client.get("/api/notices/N-2026-002/refusal").json()
    assert body["supported"] is False
    assert client.get("/api/notices/N-2026-001/refusal").status_code == 400


def test_explanation_static_en_and_hi_with_citations():
    for locale in ("en", "hi"):
        body = client.get(f"/api/ai/explanation/N-2026-001", params={"locale": locale}).json()
        assert body["source"] == "static"
        assert body["degraded"] is False
        assert "₹45,000" in body["content"]["plain_language"]
        assert "does not automatically mean" in body["content"]["what_this_does_not_mean"] or \
               "मतलब नहीं" in body["content"]["what_this_does_not_mean"]
        assert len(body["content"]["possible_reasons"]) >= 3
        citations = body["citations"]
        assert len(citations) >= 3
        first = citations[0]
        assert first["official_url"].startswith("http")
        assert first["verification"] in ("pending", "verified")
        assert first["excerpt"]


def test_explanation_unsupported_notice_is_400():
    assert client.get("/api/ai/explanation/N-2026-002").status_code == 400
