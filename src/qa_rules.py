"""QA rules for copy type focus, length risk, and overall status."""

from __future__ import annotations

from .utils import parse_optional_int, safe_text


COPY_TYPE_QA_RULES: dict[str, list[str]] = {
    "App 按钮": [
        "是否简短",
        "是否以动作为导向",
        "是否适合放在按钮中",
        "是否过长导致 UI 风险",
    ],
    "错误提示": [
        "是否清楚说明发生了什么",
        "是否避免责备用户",
        "是否提供下一步解决建议",
        "是否语气自然",
    ],
    "Push 通知": [
        "是否自然、有吸引力",
        "是否避免过度夸张",
        "是否适合移动端通知",
        "是否保留核心信息",
    ],
    "隐私 / 权限提示": [
        "是否准确、透明",
        "是否避免误导",
        "是否适合权限请求或隐私说明",
        "是否语气可信、低风险",
    ],
    "商品标题": [
        "是否简洁",
        "是否保留核心卖点",
        "是否适合电商场景",
        "是否避免关键词堆砌",
    ],
    "商品描述": [
        "是否信息完整",
        "是否自然本地化",
        "是否符合目标语言用户阅读习惯",
        "是否避免机械直译",
    ],
    "营销短句 / Slogan": [
        "是否自然、有记忆点",
        "是否避免直译腔",
        "是否有文化适配意识",
        "是否避免可能引发误解的表达",
    ],
}


def get_qa_focus(copy_type: str) -> list[str]:
    return COPY_TYPE_QA_RULES.get(copy_type, COPY_TYPE_QA_RULES["商品描述"])


def estimate_text_width_px(text: str, target_language: str) -> float:
    latin_width = 7.2 if target_language != "fr" else 7.6
    cjk_width = 12.0 if target_language == "ja" else 11.0
    width = 0.0
    for char in text:
        if char.isspace():
            width += 4.0
        elif ord(char) > 255:
            width += cjk_width
        else:
            width += latin_width
    return width


def check_length_risk(
    localized_text: str,
    source_text: str,
    target_language: str,
    max_chars: object = None,
    ui_width_px: object = None,
) -> tuple[str, str]:
    localized = safe_text(localized_text)
    source = safe_text(source_text)
    max_chars_value = parse_optional_int(max_chars)
    ui_width_value = parse_optional_int(ui_width_px)

    if max_chars_value:
        length = len(localized)
        ratio = length / max_chars_value
        if length > max_chars_value:
            return "high", f"译文 {length} 字符，超过上限 {max_chars_value}。"
        if ratio >= 0.8:
            return "medium", f"译文 {length} 字符，已达到上限的 {ratio:.0%}。"
        return "low", f"译文 {length} 字符，低于上限 {max_chars_value}。"

    if ui_width_value:
        estimated_width = estimate_text_width_px(localized, target_language)
        ratio = estimated_width / ui_width_value
        if ratio > 1:
            return "high", f"估算宽度 {estimated_width:.0f}px，可能超过 UI 宽度 {ui_width_value}px。"
        if ratio >= 0.8:
            return "medium", f"估算宽度 {estimated_width:.0f}px，接近 UI 宽度 {ui_width_value}px。"
        return "low", f"估算宽度 {estimated_width:.0f}px，低于 UI 宽度 {ui_width_value}px。"

    source_length = max(len(source), 1)
    expansion_ratio = len(localized) / source_length
    medium_threshold = 1.25 if target_language == "ja" else 2.1
    high_threshold = 1.5 if target_language == "ja" else 2.6
    if expansion_ratio >= high_threshold:
        return "high", f"译文/原文长度比为 {expansion_ratio:.1f}，存在明显膨胀。"
    if expansion_ratio >= medium_threshold:
        return "medium", f"译文/原文长度比为 {expansion_ratio:.1f}，略偏长。"
    return "low", f"译文/原文长度比为 {expansion_ratio:.1f}，处于正常范围。"


def determine_overall_status(
    model_error: str = "",
    length_risk: str = "low",
    terminology_status: str = "pass",
) -> str:
    if model_error:
        return "fail"
    if length_risk == "high" or terminology_status == "warning":
        return "warning"
    return "pass"
