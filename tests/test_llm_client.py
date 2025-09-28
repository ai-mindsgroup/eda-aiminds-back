import pytest

import src.settings as settings
from src.api.llm_client import GrokLLMConfig, LLMClient, LLMProvider


def test_llm_client_requires_grok_api_key(monkeypatch):
    monkeypatch.setattr(settings, "GROK_API_KEY", None)
    with pytest.raises(RuntimeError):
        LLMClient()


def test_llm_client_generate_uses_grok(monkeypatch):
    monkeypatch.setattr(settings, "GROK_API_KEY", "test-key")
    monkeypatch.setattr(settings, "GROK_API_BASE", "https://api.test")
    monkeypatch.setattr(settings, "GROK_DEFAULT_MODEL", "grok-test")

    config = GrokLLMConfig(
        api_key="test-key",
        api_base="https://api.test",
        model="grok-test",
        temperature=0.1,
        max_tokens=128,
        timeout=5,
    )

    client = LLMClient(grok_config=config)

    def fake_post(url, headers, json, timeout):
        fake_post.called = True
        assert url.endswith("/chat/completions")
        assert headers["Authorization"] == "Bearer test-key"
        assert json["model"] == "grok-test"

        class Response:
            status_code = 200

            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}

        return Response()

    fake_post.called = False
    monkeypatch.setattr("src.api.llm_client.requests.post", fake_post)

    result = client.generate("system", "user question")

    assert fake_post.called is True
    assert result.content == "ok"
    assert result.raw["choices"][0]["message"]["content"] == "ok"


def test_llm_client_openai_disabled(monkeypatch):
    monkeypatch.setattr(settings, "GROK_API_KEY", "dummy")
    with pytest.raises(NotImplementedError):
        LLMClient(provider=LLMProvider.OPENAI)
