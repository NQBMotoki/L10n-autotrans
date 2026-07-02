"""DeepSeek API client with mock fallback and JSON parsing safeguards."""

from __future__ import annotations

import json
from typing import Any

import requests

from .schemas import LANGUAGE_NAMES, ModelResult, TermRecord


REQUIRED_MODEL_FIELDS = [
    "localized_text",
    "rationale",
    "cultural_adaptation",
    "tone_notes",
    "risk_notes",
]


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


def normalize_model_result(data: dict[str, Any]) -> ModelResult:
    values = {field: str(data.get(field, "")).strip() for field in REQUIRED_MODEL_FIELDS}
    if not values["localized_text"]:
        return ModelResult(**values, error="模型 JSON 缺少 localized_text。")
    return ModelResult(**values)


def mock_localization(
    source_text: str,
    target_language: str,
    copy_type: str,
    terms: list[TermRecord] | None = None,
    fallback_reason: str = "",
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
    return ModelResult(
        localized_text=localized,
        rationale=f"{reason} 已按“{copy_type}”场景生成自然表达。{term_hint}".strip(),
        cultural_adaptation="示例建议：根据目标市场习惯调整语气，避免机械直译。",
        tone_notes="语气保持清晰、自然，并贴近产品界面或营销场景。",
        risk_notes="这是 mock 结果，仅用于流程演示；正式使用请接入 DeepSeek API。",
    )


def call_deepseek(
    messages: list[dict[str, str]],
    api_key: str,
    base_url: str,
    model: str,
    timeout: int = 60,
) -> ModelResult:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    body = response.json()
    content = body["choices"][0]["message"]["content"]
    return normalize_model_result(extract_json_object(content))


def localize_with_model(
    messages: list[dict[str, str]],
    source_text: str,
    target_language: str,
    copy_type: str,
    api_key: str,
    base_url: str,
    model: str,
    mock_mode: bool,
    terms: list[TermRecord] | None = None,
) -> ModelResult:
    if mock_mode:
        return mock_localization(source_text, target_language, copy_type, terms)
    if not api_key:
        return mock_localization(
            source_text,
            target_language,
            copy_type,
            terms,
            fallback_reason="未提供 API Key，已自动使用 mock fallback。",
        )

    try:
        return call_deepseek(messages, api_key, base_url, model)
    except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
        message = str(exc) or exc.__class__.__name__
        if isinstance(exc, ValueError):
            return ModelResult(
                localized_text="",
                rationale="",
                cultural_adaptation="",
                tone_notes="",
                risk_notes="",
                error=f"模型返回无法解析为有效 JSON：{message}",
            )
        return mock_localization(
            source_text,
            target_language,
            copy_type,
            terms,
            fallback_reason=f"API 调用不可用，已自动使用 mock fallback：{message}",
        )
