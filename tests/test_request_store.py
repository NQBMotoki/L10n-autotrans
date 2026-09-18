from __future__ import annotations

import json

from src.request_store import (
    build_request_payload,
    create_request_record,
    request_archive_json_bytes,
    request_archive_jsonl_bytes,
)


def test_request_archive_is_replayable_without_credentials() -> None:
    messages = [
        {"role": "system", "content": "Return JSON."},
        {"role": "user", "content": "立即购买"},
    ]
    record = create_request_record(
        run_id="run-1",
        provider="openai",
        model="demo-model",
        source_text="立即购买",
        target_language="en",
        copy_type="App 按钮",
        payload=build_request_payload("openai", "demo-model", messages),
        base_url="https://example.test/v1?token=should-not-be-saved",
    )

    document = json.loads(request_archive_json_bytes([record]))
    jsonl = request_archive_jsonl_bytes([record]).decode("utf-8").strip()

    assert document["records"][0]["payload"]["messages"] == messages
    assert document["records"][0]["base_url"] == "https://example.test/v1"
    assert "should-not-be-saved" not in json.dumps(document)
    assert json.loads(jsonl)["request_id"] == record["request_id"]
    assert "api_key" not in json.dumps(document).lower()


def test_anthropic_archive_matches_system_message_shape() -> None:
    payload = build_request_payload(
        "anthropic",
        "claude-demo",
        [
            {"role": "system", "content": "Use JSON."},
            {"role": "user", "content": "立即购买"},
        ],
    )

    assert payload["system"] == "Use JSON."
    assert payload["messages"] == [{"role": "user", "content": "立即购买"}]
