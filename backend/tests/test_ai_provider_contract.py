import pytest

from app.ai.provider import ChatProvider
from app.config import Settings
from app.knowledge.embedder import AIUnavailableError


def test_missing_key_is_safe_and_does_not_construct_client():
    with pytest.raises(AIUnavailableError, match="not configured"):
        ChatProvider(Settings(openai_api_key="")).chat_json("system", "user")


def test_provider_uses_configured_timeout_and_parses_json(monkeypatch):
    seen = {}

    class FakeCompletions:
        def create(self, **kwargs):
            seen.update(kwargs)
            return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": '{"category":"unknown_income_tax_communication"}'})()})()]})()

    class FakeClient:
        def __init__(self, **kwargs):
            seen["client"] = kwargs
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr("app.ai.provider.OpenAI", FakeClient)
    result = ChatProvider(Settings(openai_api_key="test-key", openai_timeout_seconds=7.5)).chat_json("system", "user")
    assert result["category"] == "unknown_income_tax_communication"
    assert seen["client"]["timeout"] == 7.5
    assert seen["model"] == "gpt-4o-mini"
    assert seen["response_format"] == {"type": "json_object"}


def test_provider_wraps_malformed_response_as_safe_ai_failure(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "not-json"})()})()]})()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr("app.ai.provider.OpenAI", FakeClient)
    with pytest.raises(AIUnavailableError, match="chat call failed"):
        ChatProvider(Settings(openai_api_key="test-key")).chat_json("system", "user")


def test_provider_wraps_timeout_as_safe_ai_failure(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            raise TimeoutError("provider timeout")

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr("app.ai.provider.OpenAI", FakeClient)
    with pytest.raises(AIUnavailableError, match="chat call failed"):
        ChatProvider(Settings(openai_api_key="test-key")).chat_json("system", "user")
