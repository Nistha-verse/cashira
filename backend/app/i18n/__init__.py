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
        groups = integer.split(",")
        if len(groups) <= 2:
            indian = ",".join(groups)
        else:
            indian = groups[0] + "," + ",".join(groups[1:])
        # Western digits are retained; the comma grouping is Indian-style for
        # values above one lakh.
        if len(groups) > 2:
            head = groups[0]
            tail = "".join(groups[1:])
            last3, rest = tail[-3:], tail[:-3]
            indian = head + ("," + ",".join(rest[i:i + 2] for i in range(0, len(rest), 2)) if rest else "") + "," + last3
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
