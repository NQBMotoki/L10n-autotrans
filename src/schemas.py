"""Shared constants and lightweight data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


LANGUAGE_OPTIONS: dict[str, str] = {
    "en": "英语 (en)",
    "ja": "日语 (ja)",
    "fr": "法语 (fr)",
}

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "ja": "Japanese",
    "fr": "French",
}

COPY_TYPES: list[str] = [
    "App 按钮",
    "错误提示",
    "Push 通知",
    "隐私 / 权限提示",
    "商品标题",
    "商品描述",
    "营销短句 / Slogan",
]

INPUT_COLUMNS: list[str] = [
    "id",
    "source_text",
    "copy_type",
    "max_chars",
    "ui_width_px",
]

RESULT_COLUMNS: list[str] = [
    "id",
    "source_text",
    "copy_type",
    "target_language",
    "localized_text",
    "rationale",
    "cultural_adaptation",
    "tone_notes",
    "risk_notes",
    "length_risk",
    "length_risk_reason",
    "terminology_status",
    "terminology_issues",
    "overall_status",
]

DEFAULT_INPUT_ROWS: list[dict[str, Any]] = [
    {
        "id": "btn_001",
        "source_text": "立即购买",
        "copy_type": "App 按钮",
        "max_chars": 12,
        "ui_width_px": 120,
    },
    {
        "id": "err_001",
        "source_text": "网络连接失败，请稍后重试",
        "copy_type": "错误提示",
        "max_chars": 60,
        "ui_width_px": 320,
    },
    {
        "id": "push_001",
        "source_text": "你的会员优惠即将过期",
        "copy_type": "Push 通知",
        "max_chars": 80,
        "ui_width_px": 360,
    },
]


@dataclass(frozen=True)
class ModelResult:
    """Normalized model response used by the app pipeline."""

    localized_text: str
    rationale: str
    cultural_adaptation: str
    tone_notes: str
    risk_notes: str
    error: str = ""


@dataclass(frozen=True)
class TermRecord:
    """A single terminology constraint after user field mapping."""

    source_term: str
    target_term: str
    target_language: str
    note: str = ""
