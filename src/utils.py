"""General helpers for validation and data normalization."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

from .schemas import COPY_TYPES, INPUT_COLUMNS


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_env_config() -> dict[str, str]:
    """Load optional DeepSeek settings from .env without failing if absent."""

    load_dotenv(PROJECT_ROOT / ".env")
    return {
        "api_key": os.getenv("DEEPSEEK_API_KEY", "").strip(),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip(),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip(),
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
