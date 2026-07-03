from __future__ import annotations

import pandas as pd
import streamlit as st

from src.exporters import to_csv_bytes, to_excel_bytes, to_json_bytes
from src.llm_client import generate_localization, list_provider_models
from src.prompts import build_localization_messages
from src.qa_rules import check_length_risk, determine_overall_status, get_qa_focus
from src.schemas import (
    COPY_TYPES,
    DEFAULT_INPUT_ROWS,
    INPUT_COLUMNS,
    LANGUAGE_OPTIONS,
    PROVIDER_LABELS,
    PROVIDER_ORDER,
    RESULT_COLUMNS,
)
from src.terminology import (
    build_term_records,
    check_terminology,
    default_field_mapping,
    get_columns,
    summarize_terms,
    terms_for_language,
)
from src.utils import (
    drop_empty_source_rows,
    ensure_input_columns,
    load_env_config,
    parse_optional_int,
    read_uploaded_table,
    resolve_copy_type,
    safe_text,
)


st.set_page_config(page_title="L10n-autotrans", page_icon="🌐", layout="wide")


def select_index(options: list[str], selected: str | None, default: int = 0) -> int:
    if selected in options:
        return options.index(selected)
    return default


def load_input_dataframe(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame(DEFAULT_INPUT_ROWS, columns=INPUT_COLUMNS)
    return ensure_input_columns(read_uploaded_table(uploaded_file))


def render_downloads(results_df: pd.DataFrame) -> None:
    csv_data = to_csv_bytes(results_df)
    excel_data = to_excel_bytes(results_df)
    json_data = to_json_bytes(results_df)

    col_csv, col_excel, col_json = st.columns(3)
    with col_csv:
        st.download_button(
            "下载 CSV",
            data=csv_data,
            file_name="l10n_qa_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_excel:
        st.download_button(
            "下载 Excel",
            data=excel_data,
            file_name="l10n_qa_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col_json:
        st.download_button(
            "下载 JSON",
            data=json_data,
            file_name="l10n_qa_results.json",
            mime="application/json",
            use_container_width=True,
        )


def current_provider_config(env_config: dict, provider: str) -> dict[str, str]:
    return env_config["providers"].get(provider, {})


def get_cached_models(provider: str) -> list[str]:
    return st.session_state.model_cache.get(provider, [])


def set_cached_models(provider: str, models: list[str]) -> None:
    st.session_state.model_cache[provider] = models


env_config = load_env_config()
if "model_cache" not in st.session_state:
    st.session_state.model_cache = {}
if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame(columns=RESULT_COLUMNS)
for provider_key in PROVIDER_ORDER:
    session_key = f"{provider_key}_api_key_input"
    if session_key not in st.session_state:
        st.session_state[session_key] = current_provider_config(env_config, provider_key).get(
            "api_key", ""
        )

with st.sidebar:
    st.header("配置")

    default_provider = env_config["default_provider"]
    provider = st.radio(
        "Provider",
        options=PROVIDER_ORDER,
        index=select_index(PROVIDER_ORDER, default_provider),
        format_func=lambda key: PROVIDER_LABELS[key],
    )
    provider_config = current_provider_config(env_config, provider)

    api_key = ""
    selected_model = "mock"
    manual_model = ""
    fallback_to_mock = st.checkbox("Fallback to Mock when API call fails", value=True)

    if provider == "mock":
        st.caption("Mock Provider 无需 API Key 或模型选择。")
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
        refresh_clicked = st.button("Refresh models", use_container_width=True)
        if refresh_clicked:
            try:
                refreshed_models = list_provider_models(
                    provider=provider,
                    api_key=api_key,
                    base_url=provider_config.get("base_url", ""),
                    site_url=provider_config.get("site_url", ""),
                    app_name=provider_config.get("app_name", ""),
                )
                set_cached_models(provider, refreshed_models)
                st.success(f"已刷新 {len(refreshed_models)} 个模型。")
            except Exception as exc:  # noqa: BLE001 - keep UI responsive.
                st.warning(f"模型列表刷新失败：{exc}")

        cached_models = get_cached_models(provider)
        default_model = provider_config.get("default_model", "")
        model_options = cached_models.copy()
        if default_model and default_model not in model_options:
            model_options.insert(0, default_model)

        if model_options:
            selected_model = st.selectbox("Model", model_options)
        else:
            selected_model = ""
            st.caption("暂无模型列表。请刷新模型，或使用手动模型名。")

        manual_model = st.text_input(
            "Manual model override",
            value="",
            placeholder="例如从 Provider 官方文档复制当前可用模型名",
        ).strip()
        selected_model = manual_model or selected_model

    target_languages = st.multiselect(
        "目标语言",
        options=list(LANGUAGE_OPTIONS.keys()),
        default=["en"],
        format_func=lambda code: LANGUAGE_OPTIONS[code],
    )
    default_copy_type = st.selectbox("默认文案类型", COPY_TYPES, index=0)

    st.divider()
    st.subheader("术语表")
    terms_upload = st.file_uploader("上传术语表 CSV", type=["csv"], key="terms_upload")

    term_records = []
    if terms_upload is not None:
        try:
            terms_df = pd.read_csv(terms_upload)
            columns = get_columns(terms_df)
            mapping = default_field_mapping(terms_df)
            if not columns:
                st.warning("术语表为空。")
            else:
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
                    index=select_index(optional_columns, mapping["target_language"], 0),
                )
                note_choice = st.selectbox(
                    "备注列",
                    optional_columns,
                    index=select_index(optional_columns, mapping["note"], 0),
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
        except Exception as exc:  # noqa: BLE001 - show readable app-level error.
            st.error(f"术语表读取失败：{exc}")

st.title("L10n-autotrans")
st.caption("中文产品文案多语言本地化生成与 QA 工具")

input_upload = st.file_uploader("上传输入表格 CSV / Excel", type=["csv", "xlsx", "xls"])
try:
    input_df = load_input_dataframe(input_upload)
except Exception as exc:  # noqa: BLE001 - keep Streamlit app responsive.
    st.error(f"输入表格读取失败：{exc}")
    input_df = pd.DataFrame(DEFAULT_INPUT_ROWS, columns=INPUT_COLUMNS)

edited_df = st.data_editor(
    input_df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "copy_type": st.column_config.SelectboxColumn("copy_type", options=COPY_TYPES),
        "max_chars": st.column_config.NumberColumn("max_chars", min_value=1, step=1),
        "ui_width_px": st.column_config.NumberColumn("ui_width_px", min_value=1, step=1),
    },
)
edited_df = ensure_input_columns(edited_df)

run_clicked = st.button("运行本地化与 QA", type="primary", use_container_width=True)
if run_clicked:
    clean_df = drop_empty_source_rows(edited_df)
    if not target_languages:
        st.warning("请至少选择一种目标语言。")
    elif clean_df.empty:
        st.warning("请至少输入一条中文原文。")
    elif provider != "mock" and not api_key:
        st.warning("当前真实 Provider 缺少 API Key。请输入 API Key，或切换到 Mock。")
    elif provider != "mock" and not selected_model:
        st.warning("当前真实 Provider 缺少模型名。请刷新模型、手动输入模型名，或切换到 Mock。")
    else:
        rows = []
        total = len(clean_df) * len(target_languages)
        progress = st.progress(0, text="正在生成本地化结果...")
        completed = 0
        fallback_count = 0

        for _, row in clean_df.iterrows():
            source_text = safe_text(row.get("source_text"))
            copy_type = resolve_copy_type(row.get("copy_type"), default_copy_type)
            max_chars = parse_optional_int(row.get("max_chars"))
            ui_width_px = parse_optional_int(row.get("ui_width_px"))

            for target_language in target_languages:
                applicable_terms = terms_for_language(term_records, target_language, source_text)
                qa_focus = get_qa_focus(copy_type)
                messages = build_localization_messages(
                    source_text=source_text,
                    target_language=target_language,
                    copy_type=copy_type,
                    qa_focus=qa_focus,
                    terminology_constraints=applicable_terms,
                    max_chars=max_chars,
                    ui_width_px=ui_width_px,
                )
                model_result = generate_localization(
                    provider=provider,
                    model=selected_model,
                    api_key=api_key,
                    base_url=provider_config.get("base_url", ""),
                    messages=messages,
                    source_text=source_text,
                    target_language=target_language,
                    copy_type=copy_type,
                    fallback_to_mock=fallback_to_mock,
                    terms=applicable_terms,
                    site_url=provider_config.get("site_url", ""),
                    app_name=provider_config.get("app_name", ""),
                )
                if model_result.provider_status == "fallback":
                    fallback_count += 1

                if model_result.error:
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
                        terms=term_records,
                    )

                overall_status = determine_overall_status(
                    model_error=model_result.error,
                    length_risk=length_risk,
                    terminology_status=terminology_status,
                )
                rows.append(
                    {
                        "id": safe_text(row.get("id")),
                        "source_text": source_text,
                        "copy_type": copy_type,
                        "target_language": target_language,
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
                        "overall_status": overall_status,
                    }
                )
                completed += 1
                progress.progress(completed / total, text=f"已完成 {completed}/{total}")

        progress.empty()
        st.session_state.results_df = pd.DataFrame(rows, columns=RESULT_COLUMNS)
        if fallback_count:
            st.warning(f"本次有 {fallback_count} 条结果来自 Mock fallback。")
        st.success("本地化与 QA 已完成。")

st.subheader("结果总览")
results_df = st.session_state.results_df
if results_df.empty:
    st.info("暂无结果。运行后将在这里显示 QA 报告。")
else:
    status_filter = st.multiselect(
        "筛选状态",
        options=["pass", "warning", "fail"],
        default=["pass", "warning", "fail"],
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
    st.dataframe(filtered_df[display_columns], use_container_width=True, hide_index=True)

    with st.expander("逐条查看"):
        for _, result in filtered_df.iterrows():
            st.markdown(
                f"**{safe_text(result['id']) or '(no id)'} · "
                f"{result['target_language']} · {result['overall_status']}**"
            )
            st.caption(f"Provider: {result['provider']} · Model: {result['model']}")
            st.write(result["localized_text"])
            st.caption(result["length_risk_reason"])
            if safe_text(result["terminology_issues"]):
                st.warning(result["terminology_issues"])
            if safe_text(result["risk_notes"]):
                st.info(result["risk_notes"])

    st.subheader("导出")
    render_downloads(filtered_df)

if term_records:
    with st.expander("当前术语表"):
        st.dataframe(summarize_terms(term_records), use_container_width=True, hide_index=True)
