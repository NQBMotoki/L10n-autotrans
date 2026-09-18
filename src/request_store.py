"""Portable, API-key-free storage for requests sent to an LLM.

The Streamlit session keeps request records in memory. Users can explicitly
download the records as JSON or JSONL for audit, debugging, or later replay.
Secrets are intentionally not part of the record shape.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4


REQUEST_SCHEMA_VERSION = "l10n-autotrans.request.v1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "role": str(message.get("role", "")),
            "content": str(message.get("content", "")),
        }
        for message in messages
    ]


def _safe_base_url(base_url: str) -> str:
    """Keep an endpoint hint while dropping query strings or fragments."""

    value = str(base_url or "").strip()
    if not value:
        return ""
    parsed = urlsplit(value)
    if parsed.scheme and parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    return value.split("?", 1)[0].split("#", 1)[0]


def _redact_sensitive_text(value: str, sensitive_values: list[str] | None) -> str:
    redacted = str(value or "")
    for sensitive_value in sensitive_values or []:
        secret = str(sensitive_value or "")
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


def build_request_payload(
    provider: str,
    model: str,
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    """Return the provider-neutral payload shape used by the current clients.

    The payload deliberately excludes credentials and transport-only headers.
    For Anthropic, the system message is separated in the same way as the
    actual SDK call, making the saved request useful for reproducing a call.
    """

    clean_messages = _clean_messages(messages)
    if provider == "anthropic":
        system_parts = [
            message["content"]
            for message in clean_messages
            if message["role"] == "system"
        ]
        chat_messages = [
            message
            for message in clean_messages
            if message["role"] in {"user", "assistant"}
        ]
        return {
            "model": model,
            "max_tokens": 1200,
            "temperature": 0.3,
            "system": "\n\n".join(system_parts) if system_parts else None,
            "messages": chat_messages,
        }

    return {
        "model": model,
        "messages": clean_messages,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }


def create_request_record(
    *,
    run_id: str,
    provider: str,
    model: str,
    source_text: str,
    target_language: str,
    copy_type: str,
    payload: dict[str, Any],
    base_url: str = "",
) -> dict[str, Any]:
    """Create one independent request record without storing an API key."""

    canonical_payload = json.dumps(
        {
            "provider": provider,
            "model": model,
            "payload": payload,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "request_id": uuid4().hex,
        "run_id": run_id,
        "created_at": _now_iso(),
        "provider": provider,
        "model": model,
        "base_url": _safe_base_url(base_url),
        "target_language": target_language,
        "copy_type": copy_type,
        "source_text": source_text,
        "dispatch_status": "simulated" if provider == "mock" else "pending",
        "provider_status": "pending",
        "request_sha256": hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest(),
        "payload": payload,
    }


def complete_request_record(
    record: dict[str, Any],
    *,
    provider_status: str,
    result_provider: str,
    error: str = "",
    sensitive_values: list[str] | None = None,
) -> dict[str, Any]:
    """Attach outcome metadata after the provider call finishes."""

    record["completed_at"] = _now_iso()
    record["dispatch_status"] = (
        "simulated" if record["provider"] == "mock" else "sent"
    )
    record["provider_status"] = provider_status
    record["result_provider"] = result_provider
    if error:
        record["error"] = _redact_sensitive_text(error, sensitive_values)
    return record


def request_archive_json_bytes(records: list[dict[str, Any]]) -> bytes:
    """Serialize request records as a versioned JSON document."""

    document = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "exported_at": _now_iso(),
        "records": records,
    }
    return json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8")


def request_archive_jsonl_bytes(records: list[dict[str, Any]]) -> bytes:
    """Serialize one request record per line for logs and data pipelines."""

    lines = [
        json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        for record in records
    ]
    return ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")


def request_summary_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a compact display table while keeping full payloads downloadable."""

    return [
        {
            "request_id": record.get("request_id", ""),
            "run_id": record.get("run_id", ""),
            "created_at": record.get("created_at", ""),
            "provider": record.get("provider", ""),
            "model": record.get("model", ""),
            "base_url": record.get("base_url", ""),
            "target_language": record.get("target_language", ""),
            "source_text": record.get("source_text", ""),
            "dispatch_status": record.get("dispatch_status", ""),
            "provider_status": record.get("provider_status", ""),
            "request_sha256": record.get("request_sha256", ""),
        }
        for record in records
    ]
