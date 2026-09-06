from app.workflows.handlers import IncomeMismatch143Handler, Scrutiny142Handler, SafeStopHandler, get_workflow_handler
from app.routers import workflow as workflow_router


def test_supported_workflows_share_the_handler_contract():
    for handler in (IncomeMismatch143Handler(), Scrutiny142Handler()):
        assert all(callable(getattr(handler, name)) for name in ("get_questions", "resolve", "get_evidence", "generate_response", "review"))


def test_unimplemented_workflow_is_a_safe_stop_handler():
    handler = get_workflow_handler("defective_return_139_9")
    assert isinstance(handler, SafeStopHandler)
    assert handler.get_questions({})["status"] == "safe_stop"


def test_generic_questions_dispatches_through_resolved_handler(monkeypatch):
    calls = []

    class SpyHandler:
        def get_questions(self, notice, locale="en", answers=None):
            calls.append((notice["id"], locale))
            return {"questions": [{"id": "from-handler"}]}

    monkeypatch.setattr(workflow_router, "get_workflow_handler", lambda category: SpyHandler())
    response = workflow_router.questions("N-2026-001", "hi")
    assert response == {"questions": [{"id": "from-handler"}]}
    assert calls == [("N-2026-001", "hi")]
