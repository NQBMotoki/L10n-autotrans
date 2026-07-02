"""Prompt construction for localization and QA generation."""

from __future__ import annotations

import json

from .schemas import LANGUAGE_NAMES, TermRecord


def format_terminology_constraints(terms: list[TermRecord]) -> str:
    if not terms:
        return "无术语约束。"
    payload = [
        {
            "source_term": term.source_term,
            "target_term": term.target_term,
            "note": term.note,
        }
        for term in terms
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_localization_messages(
    source_text: str,
    target_language: str,
    copy_type: str,
    qa_focus: list[str],
    terminology_constraints: list[TermRecord],
    max_chars: int | None = None,
    ui_width_px: int | None = None,
) -> list[dict[str, str]]:
    language_name = LANGUAGE_NAMES.get(target_language, target_language)
    constraints = format_terminology_constraints(terminology_constraints)
    length_notes = []
    if max_chars:
        length_notes.append(f"最大字符数：{max_chars}")
    if ui_width_px:
        length_notes.append(f"UI 控件宽度：{ui_width_px}px")
    if not length_notes:
        length_notes.append("未提供硬性长度限制，请控制译文自然且不过度膨胀。")

    system = (
        "You are a senior product localization specialist. "
        "Return only valid JSON. Do not wrap the JSON in Markdown. "
        "The JSON field localized_text must be written in the target language. "
        "The JSON fields rationale, cultural_adaptation, tone_notes, and risk_notes "
        "must be written in Simplified Chinese."
    )
    user = f"""
请将以下中文产品文案本地化为 {language_name}。

中文原文：
{source_text}

文案类型：
{copy_type}

QA 关注点：
{chr(10).join(f"- {item}" for item in qa_focus)}

长度与 UI 约束：
{chr(10).join(f"- {item}" for item in length_notes)}

术语约束：
{constraints}

要求：
- 不是逐字直译，而是适合目标语言和目标市场用户的自然表达。
- 如果术语约束适用，应优先使用指定 target_term。
- 注意语气、文化适配、移动端或电商场景可读性。
- 字段语言要求：
  - localized_text：必须使用目标语言 {language_name}。
  - rationale：必须使用简体中文解释译法。
  - cultural_adaptation：必须使用简体中文说明文化适配建议。
  - tone_notes：必须使用简体中文说明语气。
  - risk_notes：必须使用简体中文说明潜在风险。
- 输出必须是严格 JSON，且只包含以下字段：
  - localized_text
  - rationale
  - cultural_adaptation
  - tone_notes
  - risk_notes

JSON 示例结构：
{{
  "localized_text": "目标语言译文",
  "rationale": "用简体中文说明为什么这样本地化。",
  "cultural_adaptation": "用简体中文说明文化适配建议。",
  "tone_notes": "用简体中文说明语气是否自然、是否符合场景。",
  "risk_notes": "用简体中文说明潜在风险或需要人工复核的点。"
}}
""".strip()
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
