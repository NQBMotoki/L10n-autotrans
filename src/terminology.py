"""Terminology table parsing and consistency checks."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from .schemas import TermRecord
from .utils import safe_text


def get_columns(df: pd.DataFrame) -> list[str]:
    return [str(column) for column in df.columns]


def guess_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    lowered = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def default_field_mapping(df: pd.DataFrame) -> dict[str, str | None]:
    columns = get_columns(df)
    return {
        "source_term": guess_column(columns, ["source_term", "source", "zh", "中文术语"]),
        "target_language": guess_column(columns, ["target_language", "language", "lang", "目标语言"]),
        "target_term": guess_column(columns, ["target_term", "target", "translation", "目标术语"]),
        "note": guess_column(columns, ["note", "notes", "comment", "备注"]),
    }


def build_term_records(
    df: pd.DataFrame,
    source_col: str,
    target_col: str,
    language_col: str | None = None,
    note_col: str | None = None,
    fallback_language: str | None = None,
) -> list[TermRecord]:
    records: list[TermRecord] = []
    for _, row in df.iterrows():
        source_term = safe_text(row.get(source_col))
        target_term = safe_text(row.get(target_col))
        target_language = safe_text(row.get(language_col)) if language_col else safe_text(fallback_language)
        note = safe_text(row.get(note_col)) if note_col else ""
        if not source_term or not target_term or not target_language:
            continue
        records.append(
            TermRecord(
                source_term=source_term,
                target_term=target_term,
                target_language=target_language.lower(),
                note=note,
            )
        )
    return records


def terms_for_language(
    terms: list[TermRecord],
    target_language: str,
    source_text: str | None = None,
) -> list[TermRecord]:
    filtered = [term for term in terms if term.target_language == target_language]
    if source_text is None:
        return filtered
    return [term for term in filtered if term.source_term in source_text]


def check_terminology(
    source_text: str,
    localized_text: str,
    target_language: str,
    terms: list[TermRecord],
) -> tuple[str, str]:
    applicable_terms = terms_for_language(terms, target_language, source_text)
    if not applicable_terms:
        return "pass", ""

    missing: list[str] = []
    localized_lower = localized_text.lower()
    for term in applicable_terms:
        if term.target_term.lower() not in localized_lower:
            missing.append(f"{term.source_term} -> {term.target_term}")

    if missing:
        return "warning", "缺少指定术语：" + "；".join(missing)
    return "pass", "命中所有适用术语。"


def summarize_terms(terms: list[TermRecord]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = [
        {
            "source_term": term.source_term,
            "target_language": term.target_language,
            "target_term": term.target_term,
            "note": term.note,
        }
        for term in terms
    ]
    return pd.DataFrame(rows)
