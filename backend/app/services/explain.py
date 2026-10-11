"""Single-location, template-based plain-language explanations."""

from __future__ import annotations

from typing import Any

TEMPLATES = {
    "missing_or_invalid_data": "We do not have enough clean cash-flow records right now, so we used the standard monthly EMI.",
    "lower_capacity": "The recent outlook is softer than usual, so the payment is nearer the lower end of your agreed range.",
    "higher_capacity": "The recent outlook is stronger than usual, so the payment can be nearer the upper end of your agreed range.",
    "steady_capacity": "The recent outlook is close to usual, so the payment stays near the middle of your agreed range.",
    "cash_flow_position": "We used a transparent cash-flow rule: the 30-day forecast is compared with your trailing monthly net average.",
}


def explain_recommendation(reasons: list[dict[str, Any]]) -> str:
    selected = []
    for reason in reasons:
        code = reason.get("code")
        template = TEMPLATES.get(code)
        if template and template not in selected:
            selected.append(template)
    if not selected:
        selected.append("We used your available cash-flow records to set a monthly payment within the agreed range.")
    return " ".join(selected[:3])


def explain_recommendation_translated(reasons: list[dict[str, Any]], lang: str = "en") -> str:
    from ..i18n import t

    selected = []
    for reason in reasons:
        key = f"explanation.{reason.get('code')}"
        translated = t(key, lang)
        if translated != key and translated not in selected:
            selected.append(translated)
    return " ".join(selected[:3]) or t("explanation.cash_flow_position", lang)
