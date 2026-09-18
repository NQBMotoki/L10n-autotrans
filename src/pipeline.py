"""Application-independent localization and QA pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from uuid import uuid4

import pandas as pd

from .llm_client import generate_localization
from .prompts import build_localization_messages
from .qa_rules import check_length_risk, determine_overall_status, get_qa_focus
from .request_store import (
    build_request_payload,
    complete_request_record,
    create_request_record,
)
from .schemas import RESULT_COLUMNS, TermRecord
from .terminology import check_terminology, terms_for_language
from .utils import (
    drop_empty_source_rows,
    parse_optional_int,
    resolve_copy_type,
    safe_text,
)


ProgressCallback = Callable[[int, int], None]


@dataclass
class BatchResult:
    """Outputs of one run, kept separate so the UI can choose what to persist."""

    rows: list[dict[str, Any]]
    request_records: list[dict[str, Any]]
    run_id: str
    fallback_count: int = 0
    error_count: int = 0


def run_localization_batch(
    input_df: pd.DataFrame,
    *,
    target_languages: list[str],
    default_copy_type: str,
    provider: str,
    model: str,
    api_key: str,
    base_url: str,
    fallback_to_mock: bool,
    terms: list[TermRecord],
    site_url: str = "",
    app_name: str = "",
    on_progress: ProgressCallback | None = None,
) -> BatchResult:
    """Generate localized rows and record every model request independently."""

    run_id = uuid4().hex
    clean_df = drop_empty_source_rows(input_df)
    rows: list[dict[str, Any]] = []
    request_records: list[dict[str, Any]] = []
    fallback_count = 0
    error_count = 0
    total = len(clean_df) * len(target_languages)
    completed = 0

    for _, row in clean_df.iterrows():
        source_text = safe_text(row.get("source_text"))
        copy_type = resolve_copy_type(row.get("copy_type"), default_copy_type)
        max_chars = parse_optional_int(row.get("max_chars"))
        ui_width_px = parse_optional_int(row.get("ui_width_px"))

        for target_language in target_languages:
            applicable_terms = terms_for_language(terms, target_language, source_text)
            messages = build_localization_messages(
                source_text=source_text,
                target_language=target_language,
                copy_type=copy_type,
                qa_focus=get_qa_focus(copy_type),
                terminology_constraints=applicable_terms,
                max_chars=max_chars,
                ui_width_px=ui_width_px,
            )
            request_record = create_request_record(
                run_id=run_id,
                provider=provider,
                model=model,
                source_text=source_text,
                target_language=target_language,
                copy_type=copy_type,
                payload=build_request_payload(provider, model, messages),
                base_url=base_url,
            )
            request_records.append(request_record)

            model_result = generate_localization(
                provider=provider,
                model=model,
                api_key=api_key,
                base_url=base_url,
                messages=messages,
                source_text=source_text,
                target_language=target_language,
                copy_type=copy_type,
                fallback_to_mock=fallback_to_mock,
                terms=applicable_terms,
                site_url=site_url,
                app_name=app_name,
            )
            complete_request_record(
                request_record,
                provider_status=model_result.provider_status,
                result_provider=model_result.provider,
                error=model_result.error,
                sensitive_values=[api_key],
            )

            if model_result.provider_status == "fallback":
                fallback_count += 1
            if model_result.error:
                error_count += 1
                length_risk = "high"
                length_reason = "模型未生成可检查的译文。"
                terminology_status = "pass"
                terminology_issues = ""
            else:
                length_risk, length_reason = check_length_risk(
                    localized_text=model_result.localized_text,
                    source_text=source_text,
                    target_language=target_language,
                    max_chars=max_chars,
                    ui_width_px=ui_width_px,
                )
                terminology_status, terminology_issues = check_terminology(
                    source_text=source_text,
                    localized_text=model_result.localized_text,
                    target_language=target_language,
                    terms=terms,
                )

            rows.append(
                {
                    "id": safe_text(row.get("id")),
                    "source_text": source_text,
                    "copy_type": copy_type,
                    "target_language": target_language,
                    "request_id": request_record["request_id"],
                    "provider": model_result.provider,
                    "model": model_result.model,
                    "provider_status": model_result.provider_status,
                    "localized_text": model_result.localized_text,
                    "rationale": model_result.rationale,
                    "cultural_adaptation": model_result.cultural_adaptation,
                    "tone_notes": model_result.tone_notes,
                    "risk_notes": model_result.error or model_result.risk_notes,
                    "length_risk": length_risk,
                    "length_risk_reason": length_reason,
                    "terminology_status": terminology_status,
                    "terminology_issues": terminology_issues,
                    "overall_status": determine_overall_status(
                        model_error=model_result.error,
                        length_risk=length_risk,
                        terminology_status=terminology_status,
                    ),
                }
            )
            completed += 1
            if on_progress:
                on_progress(completed, total)

    return BatchResult(
        rows=rows,
        request_records=request_records,
        run_id=run_id,
        fallback_count=fallback_count,
        error_count=error_count,
    )


def result_dataframe(batch_result: BatchResult) -> pd.DataFrame:
    """Normalize pipeline output to the stable result schema used by exports."""

    return pd.DataFrame(batch_result.rows, columns=RESULT_COLUMNS)
