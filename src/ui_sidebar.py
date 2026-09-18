"""Streamlit sidebar configuration components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import streamlit as st

from .llm_client import list_provider_models
from .schemas import COPY_TYPES, LANGUAGE_OPTIONS, PROVIDER_LABELS, PROVIDER_ORDER
from .terminology import build_term_records, default_field_mapping, get_columns


@dataclass(frozen=True)
class SidebarSelection:
    provider: str
    provider_config: dict[str, str]
    api_key: str
    selected_model: str
    fallback_to_mock: bool
    target_languages: list[str]
    default_copy_type: str
    term_records: list


def select_index(options: list[str], selected: str | None, default: int = 0) -> int:
    if selected in options:
        return options.index(selected)
    return default


def initialize_session_state(env_config: dict[str, Any]) -> None:
    if "model_cache" not in st.session_state:
        st.session_state.model_cache = {}
    if "request_records" not in st.session_state:
        st.session_state.request_records = []
    for provider_key in PROVIDER_ORDER:
        session_key = f"{provider_key}_api_key_input"
        if session_key not in st.session_state:
            st.session_state[session_key] = (
                env_config["providers"].get(provider_key, {}).get("api_key", "")
            )


def current_provider_config(env_config: dict[str, Any], provider: str) -> dict[str, str]:
    return env_config["providers"].get(provider, {})


def _render_terminology_block() -> list:
    st.divider()
    st.subheader("术语表")
    terms_upload = st.file_uploader("上传术语表 CSV", type=["csv"], key="terms_upload")
    term_records = []

    if terms_upload is None:
        return term_records

    try:
        terms_df = pd.read_csv(terms_upload)
        columns = get_columns(terms_df)
        mapping = default_field_mapping(terms_df)
        if not columns:
            st.warning("术语表为空。")
            return term_records

        source_col = st.selectbox(
            "中文源术语列",
            columns,
            index=select_index(columns, mapping["source_term"]),
        )
        target_col = st.selectbox(
            "目标术语列",
            columns,
            index=select_index(columns, mapping["target_term"]),
        )

        optional_columns = ["无"] + columns
        language_choice = st.selectbox(
            "目标语言列",
            optional_columns,
            index=select_index(optional_columns, mapping["target_language"]),
        )
        note_choice = st.selectbox(
            "备注列",
            optional_columns,
            index=select_index(optional_columns, mapping["note"]),
        )
        language_col = None if language_choice == "无" else language_choice
        note_col = None if note_choice == "无" else note_choice

        fallback_language = None
        if language_col is None:
            fallback_language = st.selectbox(
                "这份术语表对应的目标语言",
                list(LANGUAGE_OPTIONS.keys()),
                format_func=lambda code: LANGUAGE_OPTIONS[code],
            )

        term_records = build_term_records(
            terms_df,
            source_col=source_col,
            target_col=target_col,
            language_col=language_col,
            note_col=note_col,
            fallback_language=fallback_language,
        )
        if term_records:
            st.caption(f"已加载 {len(term_records)} 条术语。")
        else:
            st.warning("未识别到有效术语，请检查字段映射。")
    except Exception as exc:  # noqa: BLE001 - show a readable app-level error.
        st.error(f"术语表读取失败：{exc}")
    return term_records


def render_sidebar(env_config: dict[str, Any]) -> SidebarSelection:
    """Render all run configuration controls in one independently testable block."""

    initialize_session_state(env_config)
    with st.sidebar:
        st.header("配置")
        demo_mode = bool(env_config.get("demo_mode", False))
        provider_options = ["mock"] if demo_mode else PROVIDER_ORDER
        default_provider = "mock" if demo_mode else env_config["default_provider"]
        provider = st.radio(
            "模型服务商",
            options=provider_options,
            index=select_index(provider_options, default_provider),
            format_func=lambda key: PROVIDER_LABELS[key],
        )
        provider_config = current_provider_config(env_config, provider)

        api_key = ""
        selected_model = "mock"
        fallback_to_mock = st.checkbox("API 调用失败时自动回退到 Mock", value=True)

        if demo_mode:
            st.info("公开演示模式：仅使用内置 Mock，不需要 API Key 或外部模型服务。")
        elif provider == "mock":
            st.caption("Mock 服务商无需 API Key 或模型选择。")
        else:
            session_key = f"{provider}_api_key_input"
            if st.button("清除当前 API Key", use_container_width=True):
                st.session_state[session_key] = ""
                st.rerun()

            api_key = st.text_input(
                f"{PROVIDER_LABELS[provider]} API Key",
                type="password",
                key=session_key,
                placeholder="可临时输入，不会写入本地文件",
            )

            st.subheader("模型")
            if st.button("刷新模型列表", use_container_width=True):
                try:
                    refreshed_models = list_provider_models(
                        provider=provider,
                        api_key=api_key,
                        base_url=provider_config.get("base_url", ""),
                        site_url=provider_config.get("site_url", ""),
                        app_name=provider_config.get("app_name", ""),
                    )
                    st.session_state.model_cache[provider] = refreshed_models
                    st.success(f"已刷新 {len(refreshed_models)} 个模型。")
                except Exception as exc:  # noqa: BLE001 - keep the UI responsive.
                    st.warning(f"模型列表刷新失败：{exc}")

            cached_models = st.session_state.model_cache.get(provider, [])
            default_model = provider_config.get("default_model", "")
            model_options = cached_models.copy()
            if default_model and default_model not in model_options:
                model_options.insert(0, default_model)
            if model_options:
                selected_model = st.selectbox("模型", model_options)
            else:
                selected_model = ""
                st.caption("暂无模型列表。请刷新模型，或使用手动模型名。")

            manual_model = st.text_input(
                "手动指定模型",
                value="",
                placeholder="例如从服务商官方文档复制当前可用模型名",
            ).strip()
            selected_model = manual_model or selected_model

        target_languages = st.multiselect(
            "目标语言",
            options=list(LANGUAGE_OPTIONS.keys()),
            default=["en"],
            format_func=lambda code: LANGUAGE_OPTIONS[code],
        )
        default_copy_type = st.selectbox("默认文案类型", COPY_TYPES, index=0)
        term_records = _render_terminology_block()

    return SidebarSelection(
        provider=provider,
        provider_config=provider_config,
        api_key=api_key,
        selected_model=selected_model,
        fallback_to_mock=fallback_to_mock,
        target_languages=target_languages,
        default_copy_type=default_copy_type,
        term_records=term_records,
    )
