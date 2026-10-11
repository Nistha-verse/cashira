"""Small translated message catalogs with English fallback."""

from __future__ import annotations

import re
from typing import Any

from . import bn, en, hi

CATALOGS = {"en": en.CATALOG, "hi": hi.CATALOG, "bn": bn.CATALOG}
SUPPORTED_LANGUAGES = set(CATALOGS)
PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def format_inr(value: Any) -> str:
    try:
        number = float(value)
        formatted = f"{number:,.2f}"
        integer, fraction = formatted.split(".")
        digits = integer.replace(",", "")
        if len(digits) <= 3:
            indian = digits
        else:
            last3, prefix = digits[-3:], digits[:-3]
            pairs = []
            while prefix:
                pairs.insert(0, prefix[-2:])
                prefix = prefix[:-2]
            indian = ",".join(pairs + [last3])
        return f"₹{indian}.{fraction}"
    except (TypeError, ValueError):
        return str(value)


def t(key: str, lang: str | None = None, **params: Any) -> str:
    selected = lang if lang in SUPPORTED_LANGUAGES else "en"
    template = CATALOGS[selected].get(key, CATALOGS["en"].get(key, key))
    prepared = dict(params)
    if "amount" in prepared:
        prepared["amount"] = format_inr(prepared["amount"])
    try:
        return template.format(**prepared)
    except (KeyError, ValueError):
        return template


def keys() -> set[str]:
    return set(CATALOGS["en"])


def placeholders(key: str, lang: str) -> set[str]:
    return set(PLACEHOLDER_RE.findall(CATALOGS[lang][key]))
