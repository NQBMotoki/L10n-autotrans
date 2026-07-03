"""General helpers for validation and data normalization."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

from .schemas import COPY_TYPES, INPUT_COLUMNS, PROVIDER_ORDER


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_env_config() -> dict[str, Any]:
    """Load optional multi-provider settings from .env without failing if absent."""

    load_dotenv(PROJECT_ROOT / ".env")
    default_provider = os.getenv("DEFAULT_PROVIDER", "mock").strip().lower()
    if default_provider not in PROVIDER_ORDER:
        default_provider = "mock"

    return {
        "default_provider": default_provider,
        "providers": {
            "mock": {
                "api_key": "",
                "base_url": "",
                "default_model": "mock",
            },
            "deepseek": {
                "api_key": os.getenv("DEEPSEEK_API_KEY", "").strip(),
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip(),
                "default_model": (
                    os.getenv("DEEPSEEK_DEFAULT_MODEL")
                    or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
                ).strip(),
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", "").strip(),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip(),
                "default_model": os.getenv("OPENAI_DEFAULT_MODEL", "").strip(),
            },
            "anthropic": {
                "api_key": os.getenv("ANTHROPIC_API_KEY", "").strip(),
                "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com").strip(),
                "default_model": os.getenv("ANTHROPIC_DEFAULT_MODEL", "").strip(),
            },
            "openrouter": {
                "api_key": os.getenv("OPENROUTER_API_KEY", "").strip(),
                "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip(),
                "default_model": os.getenv("OPENROUTER_DEFAULT_MODEL", "").strip(),
                "site_url": os.getenv("OPENROUTER_SITE_URL", "").strip(),
                "app_name": os.getenv("OPENROUTER_APP_NAME", "L10n-autotrans").strip(),
            },
        },
    }


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value).strip()


def parse_optional_int(value: Any) -> int | None:
    text = safe_text(value)
    if not text:
        return None
    try:
        parsed = int(float(text))
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def ensure_input_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in INPUT_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""
    return normalized[INPUT_COLUMNS]


def drop_empty_source_rows(df: pd.DataFrame) -> pd.DataFrame:
    if "source_text" not in df.columns:
        return df.iloc[0:0]
    mask = df["source_text"].map(safe_text).astype(bool)
    return df.loc[mask].reset_index(drop=True)


def resolve_copy_type(value: Any, default_copy_type: str) -> str:
    candidate = safe_text(value)
    if candidate in COPY_TYPES:
        return candidate
    return default_copy_type


def read_uploaded_table(uploaded_file: Any) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    raise ValueError("仅支持 CSV 或 Excel 文件。")
