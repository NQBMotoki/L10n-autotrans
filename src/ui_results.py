"""Streamlit result, export, and request-archive components."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .exporters import to_csv_bytes, to_excel_bytes, to_json_bytes
from .request_store import (
    request_archive_json_bytes,
    request_archive_jsonl_bytes,
    request_summary_rows,
)
from .schemas import LANGUAGE_OPTIONS, PROVIDER_LABELS
from .terminology import summarize_terms
from .utils import safe_text


STATUS_LABELS: dict[str, str] = {
    "pass": "通过",
    "warning": "警告",
    "fail": "失败",
}

LENGTH_RISK_LABELS: dict[str, str] = {
    "low": "低",
    "medium": "中",
    "high": "高",
}

TERMINOLOGY_STATUS_LABELS: dict[str, str] = {
    "pass": "通过",
    "warning": "警告",
}

RESULT_COLUMN_LABELS: dict[str, str] = {
    "id": "ID",
    "source_text": "中文原文",
    "copy_type": "文案类型",
    "target_language": "目标语言",
    "localized_text": "本地化文案",
    "length_risk": "长度风险",
    "terminology_status": "术语状态",
    "overall_status": "总体状态",
}

TERM_COLUMN_LABELS: dict[str, str] = {
    "source_term": "中文源术语",
    "target_language": "目标语言",
    "target_term": "目标术语",
    "note": "备注",
}


def localized_result_dataframe(results_df: pd.DataFrame) -> pd.DataFrame:
    """Return a display-only copy with Chinese labels and status values."""

    display_df = results_df.rename(columns=RESULT_COLUMN_LABELS).copy()
    display_df[RESULT_COLUMN_LABELS["target_language"]] = results_df[
        "target_language"
    ].map(LANGUAGE_OPTIONS).fillna(results_df["target_language"])
    display_df[RESULT_COLUMN_LABELS["length_risk"]] = results_df["length_risk"].map(
        LENGTH_RISK_LABELS
    ).fillna(results_df["length_risk"])
    display_df[RESULT_COLUMN_LABELS["terminology_status"]] = results_df[
        "terminology_status"
    ].map(TERMINOLOGY_STATUS_LABELS).fillna(results_df["terminology_status"])
    display_df[RESULT_COLUMN_LABELS["overall_status"]] = results_df[
        "overall_status"
    ].map(STATUS_LABELS).fillna(results_df["overall_status"])
    return display_df


def _render_result_downloads(results_df: pd.DataFrame) -> None:
    col_csv, col_excel, col_json = st.columns(3)
    with col_csv:
        st.download_button(
            "下载 CSV",
            data=to_csv_bytes(results_df),
            file_name="l10n_qa_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_excel:
        st.download_button(
            "下载 Excel",
            data=to_excel_bytes(results_df),
            file_name="l10n_qa_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col_json:
        st.download_button(
            "下载 JSON",
            data=to_json_bytes(results_df),
            file_name="l10n_qa_results.json",
            mime="application/json",
            use_container_width=True,
        )


def _render_request_archive(records: list[dict]) -> None:
    if not records:
        return

    st.subheader("模型请求归档")
    st.caption(
        "请求记录独立于结果表保存在当前会话中，可下载为 JSON / JSONL；归档不包含 API Key。"
    )
    summary = pd.DataFrame(request_summary_rows(records))
    st.dataframe(summary, use_container_width=True, hide_index=True)

    col_json, col_jsonl = st.columns(2)
    with col_json:
        st.download_button(
            "下载请求 JSON",
            data=request_archive_json_bytes(records),
            file_name="l10n_llm_requests.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_jsonl:
        st.download_button(
            "下载请求 JSONL",
            data=request_archive_jsonl_bytes(records),
            file_name="l10n_llm_requests.jsonl",
            mime="application/x-ndjson",
            use_container_width=True,
        )

    with st.expander("查看完整请求内容"):
        for record in records:
            st.markdown(
                f"**{record.get('request_id', '')}** · "
                f"{record.get('provider', '')} / {record.get('model', '')} · "
                f"{record.get('target_language', '')}"
            )
            st.json(record)


def render_results(
    results_df: pd.DataFrame,
    request_records: list[dict],
    term_records: list,
) -> None:
    """Render results, independent request records, and terminology preview."""

    st.subheader("结果总览")
    if results_df.empty:
        st.info("暂无结果。运行后将在这里显示 QA 报告。")
        return

    status_filter = st.multiselect(
        "筛选状态",
        options=["pass", "warning", "fail"],
        default=["pass", "warning", "fail"],
        format_func=lambda status: STATUS_LABELS[status],
    )
    filtered_df = results_df[results_df["overall_status"].isin(status_filter)]
    display_columns = [
        "id",
        "source_text",
        "copy_type",
        "target_language",
        "localized_text",
        "length_risk",
        "terminology_status",
        "overall_status",
    ]
    st.dataframe(
        localized_result_dataframe(filtered_df[display_columns]),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("逐条查看"):
        for _, result in filtered_df.iterrows():
            language_label = LANGUAGE_OPTIONS.get(
                result["target_language"], result["target_language"]
            )
            status_label = STATUS_LABELS.get(result["overall_status"], result["overall_status"])
            provider_label = (
                "Mock（回退）"
                if result["provider"] == "mock_fallback"
                else PROVIDER_LABELS.get(result["provider"], result["provider"])
            )
            st.markdown(
                f"**{safe_text(result['id']) or '(无 ID)'} · "
                f"{language_label} · {status_label}**"
            )
            st.caption(f"服务商：{provider_label} · 模型：{result['model']}")
            st.write(result["localized_text"])
            st.caption(result["length_risk_reason"])
            if safe_text(result["terminology_issues"]):
                st.warning(result["terminology_issues"])
            if safe_text(result["risk_notes"]):
                st.info(result["risk_notes"])

    st.subheader("导出")
    _render_result_downloads(filtered_df)
    _render_request_archive(request_records)

    if term_records:
        with st.expander("当前术语表"):
            st.dataframe(
                summarize_terms(term_records).rename(columns=TERM_COLUMN_LABELS),
                use_container_width=True,
                hide_index=True,
            )
