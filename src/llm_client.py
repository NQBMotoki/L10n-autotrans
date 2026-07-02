"""Multi-provider LLM client with mock fallback and JSON parsing safeguards."""

from __future__ import annotations

import json
from typing import Any

import requests
from anthropic import Anthropic
from openai import OpenAI

from .schemas import LANGUAGE_NAMES, ModelResult, TermRecord


REQUIRED_MODEL_FIELDS = [
    "localized_text",
    "rationale",
    "cultural_adaptation",
    "tone_notes",
    "risk_notes",
]

OPENAI_COMPATIBLE_PROVIDERS = {"deepseek", "openai", "openrouter"}


def extract_json_object(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("模型返回的 JSON 顶层不是对象。")
    return parsed


def normalize_model_result(
    data: dict[str, Any],
    provider: str,
    model: str,
    provider_status: str = "ok",
) -> ModelResult:
    values = {field: str(data.get(field, "")).strip() for field in REQUIRED_MODEL_FIELDS}
    if not values["localized_text"]:
        return ModelResult(
            **values,
            error="模型 JSON 缺少 localized_text。",
            provider=provider,
            model=model,
            provider_status="error",
        )
    return ModelResult(
        **values,
        provider=provider,
        model=model,
        provider_status=provider_status,
    )


def mock_localization(
    source_text: str,
    target_language: str,
    copy_type: str,
    terms: list[TermRecord] | None = None,
    fallback_reason: str = "",
    provider_status: str = "ok",
) -> ModelResult:
    language_name = LANGUAGE_NAMES.get(target_language, target_language)
    term_hint = ""
    if terms:
        term_hint = f" Uses required term: {terms[0].target_term}."

    examples = {
        "en": {
            "立即购买": "Buy Now",
            "网络连接失败，请稍后重试": "Connection failed. Please try again later.",
            "你的会员优惠即将过期": "Your Membership offer is ending soon.",
            "允许我们访问你的位置以推荐附近门店": "Allow location access to find nearby stores.",
            "轻薄便携蓝牙耳机，长续航低延迟": "Slim Portable Bluetooth Earbuds with Long Battery Life",
        },
        "ja": {
            "立即购买": "今すぐ購入",
            "网络连接失败，请稍后重试": "接続に失敗しました。しばらくしてからもう一度お試しください。",
            "你的会员优惠即将过期": "メンバーシップ特典の期限がまもなく終了します。",
            "允许我们访问你的位置以推荐附近门店": "近くの店舗をおすすめするため、位置情報の利用を許可してください。",
            "轻薄便携蓝牙耳机，长续航低延迟": "薄型軽量 Bluetooth イヤホン、長時間再生・低遅延",
        },
        "fr": {
            "立即购买": "Acheter maintenant",
            "网络连接失败，请稍后重试": "La connexion a échoué. Veuillez réessayer plus tard.",
            "你的会员优惠即将过期": "Votre offre d'abonnement expire bientôt.",
            "允许我们访问你的位置以推荐附近门店": "Autorisez l'accès à votre position pour trouver des magasins proches.",
            "轻薄便携蓝牙耳机，长续航低延迟": "Écouteurs Bluetooth fins et nomades, longue autonomie et faible latence",
        },
    }
    localized = examples.get(target_language, {}).get(
        source_text,
        f"[Mock {language_name}] {source_text}",
    )
    reason = fallback_reason or "Mock 模式示例结果，用于本地演示。"
    provider = "mock_fallback" if provider_status == "fallback" else "mock"
    return ModelResult(
        localized_text=localized,
        rationale=f"{reason} 已按“{copy_type}”场景生成自然表达。{term_hint}".strip(),
        cultural_adaptation="示例建议：根据目标市场习惯调整语气，避免机械直译。",
        tone_notes="语气保持清晰、自然，并贴近产品界面或营销场景。",
        risk_notes="这是 mock 结果，仅用于流程演示；正式使用请接入真实 Provider。",
        provider=provider,
        model="mock",
        provider_status=provider_status,
    )


def openrouter_headers(site_url: str = "", app_name: str = "") -> dict[str, str]:
    headers: dict[str, str] = {}
    if site_url:
        headers["HTTP-Referer"] = site_url
    if app_name:
        headers["X-Title"] = app_name
    return headers


def call_openai_compatible(
    provider: str,
    messages: list[dict[str, str]],
    api_key: str,
    base_url: str,
    model: str,
    site_url: str = "",
    app_name: str = "",
) -> ModelResult:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url.rstrip("/") if base_url else None,
        default_headers=openrouter_headers(site_url, app_name) if provider == "openrouter" else None,
    )
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    return normalize_model_result(extract_json_object(content), provider, model)


def call_anthropic(
    messages: list[dict[str, str]],
    api_key: str,
    base_url: str,
    model: str,
) -> ModelResult:
    system_parts = [message["content"] for message in messages if message["role"] == "system"]
    chat_messages = [
        {"role": message["role"], "content": message["content"]}
        for message in messages
        if message["role"] in {"user", "assistant"}
    ]
    client = Anthropic(api_key=api_key, base_url=base_url.rstrip("/") if base_url else None)
    response = client.messages.create(
        model=model,
        max_tokens=1200,
        temperature=0.3,
        system="\n\n".join(system_parts) if system_parts else None,
        messages=chat_messages,
    )
    content = "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    )
    return normalize_model_result(extract_json_object(content), "anthropic", model)


def generate_localization(
    provider: str,
    model: str,
    api_key: str,
    base_url: str,
    messages: list[dict[str, str]],
    source_text: str,
    target_language: str,
    copy_type: str,
    fallback_to_mock: bool = True,
    terms: list[TermRecord] | None = None,
    site_url: str = "",
    app_name: str = "",
) -> ModelResult:
    if provider == "mock":
        return mock_localization(source_text, target_language, copy_type, terms)

    try:
        if provider in OPENAI_COMPATIBLE_PROVIDERS:
            return call_openai_compatible(
                provider=provider,
                messages=messages,
                api_key=api_key,
                base_url=base_url,
                model=model,
                site_url=site_url,
                app_name=app_name,
            )
        if provider == "anthropic":
            return call_anthropic(messages, api_key, base_url, model)
        raise ValueError(f"Unsupported provider: {provider}")
    except Exception as exc:  # noqa: BLE001 - convert provider errors to app-level results.
        message = str(exc) or exc.__class__.__name__
        if fallback_to_mock:
            return mock_localization(
                source_text,
                target_language,
                copy_type,
                terms,
                fallback_reason=f"{provider} API 调用失败，已自动使用 Mock fallback：{message}",
                provider_status="fallback",
            )
        return ModelResult(
            localized_text="",
            rationale="",
            cultural_adaptation="",
            tone_notes="",
            risk_notes="",
            error=f"{provider} API 调用失败：{message}",
            provider=provider,
            model=model,
            provider_status="error",
        )


def list_openai_compatible_models(
    provider: str,
    api_key: str,
    base_url: str,
    site_url: str = "",
    app_name: str = "",
) -> list[str]:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url.rstrip("/") if base_url else None,
        default_headers=openrouter_headers(site_url, app_name) if provider == "openrouter" else None,
    )
    response = client.models.list()
    return sorted(model.id for model in response.data if getattr(model, "id", ""))


def list_anthropic_models(api_key: str, base_url: str) -> list[str]:
    client = Anthropic(api_key=api_key, base_url=base_url.rstrip("/") if base_url else None)
    response = client.models.list()
    data = getattr(response, "data", response)
    return sorted(model.id for model in data if getattr(model, "id", ""))


def list_openrouter_models(
    api_key: str,
    base_url: str,
    site_url: str = "",
    app_name: str = "",
) -> list[str]:
    headers = {"Authorization": f"Bearer {api_key}"}
    headers.update(openrouter_headers(site_url, app_name))
    response = requests.get(base_url.rstrip("/") + "/models", headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json().get("data", [])
    return sorted(item["id"] for item in data if item.get("id"))


def list_provider_models(
    provider: str,
    api_key: str,
    base_url: str,
    site_url: str = "",
    app_name: str = "",
) -> list[str]:
    if provider == "mock":
        return ["mock"]
    if not api_key:
        raise ValueError("请先提供当前 Provider 的 API Key。")
    if provider in {"deepseek", "openai"}:
        return list_openai_compatible_models(provider, api_key, base_url)
    if provider == "anthropic":
        return list_anthropic_models(api_key, base_url)
    if provider == "openrouter":
        return list_openrouter_models(api_key, base_url, site_url, app_name)
    raise ValueError(f"Unsupported provider: {provider}")
