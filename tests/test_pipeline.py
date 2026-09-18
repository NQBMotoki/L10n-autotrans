from __future__ import annotations

import pandas as pd

from src.pipeline import result_dataframe, run_localization_batch


def test_mock_pipeline_returns_results_and_independent_requests() -> None:
    progress: list[tuple[int, int]] = []
    input_df = pd.DataFrame(
        [
            {
                "id": "btn_001",
                "source_text": "立即购买",
                "copy_type": "App 按钮",
                "max_chars": 12,
                "ui_width_px": 120,
            }
        ]
    )

    batch = run_localization_batch(
        input_df,
        target_languages=["en", "ja"],
        default_copy_type="商品描述",
        provider="mock",
        model="mock",
        api_key="should-never-be-archived",
        base_url="",
        fallback_to_mock=True,
        terms=[],
        on_progress=lambda completed, total: progress.append((completed, total)),
    )

    results = result_dataframe(batch)
    assert len(results) == 2
    assert len(batch.request_records) == 2
    assert progress[-1] == (2, 2)
    assert set(results["request_id"]) == {
        record["request_id"] for record in batch.request_records
    }
    assert all(record["dispatch_status"] == "simulated" for record in batch.request_records)
    assert all(record["provider_status"] == "ok" for record in batch.request_records)
    assert "should-never-be-archived" not in str(batch.request_records)
