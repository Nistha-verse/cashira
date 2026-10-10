"""Optional chain anchor boundary; disabled by default."""

from __future__ import annotations

from typing import Any

from ..config import settings


def anchor_record(loan_ref: str, record_hash: str, rule_version: str) -> dict[str, Any] | None:
    """Return an anchor receipt when enabled; never block the prototype.

    The concrete web3 implementation is added only in the optional final
    chain build. With the default flag this function is a no-op.
    """

    if not settings.chain_enabled:
        return None
    return None
