from __future__ import annotations

from types import SimpleNamespace

import pytest

from src import llm_client


def test_declared_openai_client_can_initialize_without_network() -> None:
    client = llm_client.create_openai_client(
        api_key="test-api-key",
        base_url="https://api.deepseek.com",
    )

    client.close()


def test_list_openai_compatible_models_returns_sorted_ids(monkeypatch) -> None:
    captured: dict[str, object] = {}
    response = SimpleNamespace(
        data=[
            SimpleNamespace(id="deepseek-v4-pro"),
            SimpleNamespace(id=""),
            SimpleNamespace(id="deepseek-v4-flash"),
        ]
    )
    fake_client = SimpleNamespace(models=SimpleNamespace(list=lambda: response))

    def fake_create_openai_client(
        api_key: str,
        base_url: str,
        default_headers: dict[str, str] | None = None,
    ):
        captured.update(
            api_key=api_key,
            base_url=base_url,
            default_headers=default_headers,
        )
        return fake_client

    monkeypatch.setattr(llm_client, "create_openai_client", fake_create_openai_client)

    models = llm_client.list_openai_compatible_models(
        provider="deepseek",
        api_key="test-api-key",
        base_url="https://api.deepseek.com",
    )

    assert models == ["deepseek-v4-flash", "deepseek-v4-pro"]
    assert captured == {
        "api_key": "test-api-key",
        "base_url": "https://api.deepseek.com",
        "default_headers": None,
    }


def test_create_openai_client_translates_httpx_proxies_error(monkeypatch) -> None:
    class IncompatibleOpenAI:
        def __init__(self, **kwargs) -> None:
            raise TypeError("Client.__init__() got an unexpected keyword argument 'proxies'")

    monkeypatch.setattr(llm_client, "OpenAI", IncompatibleOpenAI)

    with pytest.raises(RuntimeError, match="python -m pip install --upgrade"):
        llm_client.create_openai_client(
            api_key="test-api-key",
            base_url="https://api.deepseek.com",
        )


def test_generation_reports_compatibility_error_without_mock_fallback(monkeypatch) -> None:
    class IncompatibleOpenAI:
        def __init__(self, **kwargs) -> None:
            raise TypeError("Client.__init__() got an unexpected keyword argument 'proxies'")

    monkeypatch.setattr(llm_client, "OpenAI", IncompatibleOpenAI)

    result = llm_client.generate_localization(
        provider="deepseek",
        model="deepseek-v4-flash",
        api_key="test-api-key",
        base_url="https://api.deepseek.com",
        messages=[{"role": "user", "content": "请返回 JSON"}],
        source_text="立即购买",
        target_language="en",
        copy_type="App 按钮",
        fallback_to_mock=False,
    )

    assert result.provider_status == "error"
    assert llm_client.OPENAI_HTTPX_COMPATIBILITY_MESSAGE in result.error
