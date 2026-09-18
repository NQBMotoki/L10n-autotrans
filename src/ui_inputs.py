"""Streamlit input-table components."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .schemas import COPY_TYPES, DEFAULT_INPUT_ROWS, INPUT_COLUMNS
from .utils import ensure_input_columns, read_uploaded_table


def load_input_dataframe(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame(DEFAULT_INPUT_ROWS, columns=INPUT_COLUMNS)
    return ensure_input_columns(read_uploaded_table(uploaded_file))


def render_input_editor() -> pd.DataFrame:
    """Render the upload/editor block and return normalized user input."""

    input_upload = st.file_uploader(
        "上传输入表格 CSV / Excel",
        type=["csv", "xlsx", "xls"],
        key="input_upload",
    )
    try:
        input_df = load_input_dataframe(input_upload)
    except Exception as exc:  # noqa: BLE001 - keep the page responsive.
        st.error(f"输入表格读取失败：{exc}")
        input_df = pd.DataFrame(DEFAULT_INPUT_ROWS, columns=INPUT_COLUMNS)

    edited_df = st.data_editor(
        input_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.TextColumn("ID"),
            "source_text": st.column_config.TextColumn("中文原文"),
            "copy_type": st.column_config.SelectboxColumn("文案类型", options=COPY_TYPES),
            "max_chars": st.column_config.NumberColumn("最大字符数", min_value=1, step=1),
            "ui_width_px": st.column_config.NumberColumn("UI 宽度（px）", min_value=1, step=1),
        },
    )
    return ensure_input_columns(edited_df)
