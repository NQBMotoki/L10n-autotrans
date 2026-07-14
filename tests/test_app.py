from __future__ import annotations

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.schemas import RESULT_COLUMNS


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_mock_configuration_controls_are_localized(monkeypatch) -> None:
    monkeypatch.setenv("DEFAULT_PROVIDER", "mock")
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    assert app.radio[0].label == "模型服务商"
    assert app.checkbox[0].label == "API 调用失败时自动回退到 Mock"
    assert "Provider" not in {widget.label for widget in app.radio}
    assert "Fallback to Mock when API call fails" not in {
        widget.label for widget in app.checkbox
    }


def test_deepseek_model_controls_are_localized(monkeypatch) -> None:
    monkeypatch.setenv("DEFAULT_PROVIDER", "mock")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    app.radio[0].set_value("deepseek").run()

    assert not app.exception
    assert "刷新模型列表" in {widget.label for widget in app.button}
    assert "模型" in {widget.label for widget in app.selectbox}
    assert "手动指定模型" in {widget.label for widget in app.text_input}
    assert "Refresh models" not in {widget.label for widget in app.button}
    assert "Model" not in {widget.label for widget in app.selectbox}
    assert "Manual model override" not in {widget.label for widget in app.text_input}


def test_result_table_is_localized_without_mutating_internal_values(monkeypatch) -> None:
    monkeypatch.setenv("DEFAULT_PROVIDER", "mock")
    row = {column: "" for column in RESULT_COLUMNS}
    row.update(
        {
            "source_text": "立即购买",
            "copy_type": "App 按钮",
            "target_language": "en",
            "provider": "mock_fallback",
            "model": "mock",
            "provider_status": "fallback",
            "localized_text": "Buy Now",
            "length_risk": "low",
            "length_risk_reason": "长度正常。",
            "terminology_status": "pass",
            "overall_status": "warning",
        }
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()
    app.session_state["results_df"] = pd.DataFrame([row], columns=RESULT_COLUMNS)

    app.run()

    assert not app.exception
    displayed_result = app.dataframe[1].value.iloc[0]
    assert displayed_result["目标语言"] == "英语 (en)"
    assert displayed_result["长度风险"] == "低"
    assert displayed_result["术语状态"] == "通过"
    assert displayed_result["总体状态"] == "警告"
    stored_result = app.session_state["results_df"].iloc[0]
    assert stored_result["target_language"] == "en"
    assert stored_result["length_risk"] == "low"
    assert stored_result["terminology_status"] == "pass"
    assert stored_result["overall_status"] == "warning"
