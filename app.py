"""Streamlit entry point for the L10n-autotrans demo."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.pipeline import result_dataframe, run_localization_batch
from src.schemas import RESULT_COLUMNS
from src.ui_inputs import render_input_editor
from src.ui_results import render_results
from src.ui_sidebar import render_sidebar
from src.utils import load_env_config


st.set_page_config(page_title="L10n-autotrans", page_icon="🌐", layout="wide")


def _initialize_app_state() -> None:
    if "results_df" not in st.session_state:
        st.session_state.results_df = pd.DataFrame(columns=RESULT_COLUMNS)
    if "request_records" not in st.session_state:
        st.session_state.request_records = []


def _run_batch(selection, edited_df: pd.DataFrame) -> None:
    clean_df = edited_df[
        edited_df["source_text"].fillna("").astype(str).str.strip().astype(bool)
    ]
    if not selection.target_languages:
        st.warning("请至少选择一种目标语言。")
        return
    if clean_df.empty:
        st.warning("请至少输入一条中文原文。")
        return
    if selection.provider != "mock" and not selection.api_key:
        st.warning("当前真实模型服务商缺少 API Key。请输入 API Key，或切换到 Mock。")
        return
    if selection.provider != "mock" and not selection.selected_model:
        st.warning("当前真实模型服务商缺少模型名。请刷新模型、手动输入模型名，或切换到 Mock。")
        return

    progress = st.progress(0, text="正在生成本地化结果...")

    def update_progress(completed: int, total_count: int) -> None:
        progress.progress(
            completed / total_count if total_count else 1,
            text=f"已完成 {completed}/{total_count}",
        )

    batch_result = run_localization_batch(
        clean_df,
        target_languages=selection.target_languages,
        default_copy_type=selection.default_copy_type,
        provider=selection.provider,
        model=selection.selected_model,
        api_key=selection.api_key,
        base_url=selection.provider_config.get("base_url", ""),
        fallback_to_mock=selection.fallback_to_mock,
        terms=selection.term_records,
        site_url=selection.provider_config.get("site_url", ""),
        app_name=selection.provider_config.get("app_name", ""),
        on_progress=update_progress,
    )
    progress.empty()

    st.session_state.results_df = result_dataframe(batch_result)
    st.session_state.request_records.extend(batch_result.request_records)
    if batch_result.fallback_count:
        st.warning(f"本次有 {batch_result.fallback_count} 条结果来自 Mock 回退。")
    if batch_result.error_count:
        st.warning(f"本次有 {batch_result.error_count} 条结果未能生成译文。")
    st.success("本地化与 QA 已完成。")


def main() -> None:
    _initialize_app_state()
    env_config = load_env_config()
    selection = render_sidebar(env_config)

    st.title("L10n-autotrans")
    st.caption("中文产品文案多语言本地化生成与 QA 工具")
    edited_df = render_input_editor()

    if st.button("运行本地化与 QA", type="primary", use_container_width=True):
        _run_batch(selection, edited_df)

    render_results(
        st.session_state.results_df,
        st.session_state.request_records,
        selection.term_records,
    )


main()
