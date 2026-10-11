"""Small role-aware demo-token helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any

from fastapi import HTTPException, Request

from .config import settings


def make_token(role: str, phone: str, merchant_id: int | None = None, lender_id: int | None = None) -> str:
    payload = {"role": role, "phone": phone}
    if merchant_id is not None:
        payload["merchant_id"] = merchant_id
    if lender_id is not None:
        payload["lender_id"] = lender_id
    encoded = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(settings.signing_key.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"cashira.{encoded}.{signature}"


def parse_token(token: str | None) -> dict[str, Any] | None:
    if not token or not token.startswith("cashira."):
        return None
    try:
        _, encoded, signature = token.split(".", 2)
        expected = hmac.new(settings.signing_key.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        padded = encoded + "=" * (-len(encoded) % 4)
        return json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def identity_from_request(request: Request) -> dict[str, Any] | None:
    header = request.headers.get("authorization", "")
    token = header.removeprefix("Bearer ").strip() if header else ""
    return parse_token(token)


def require_lender(request: Request) -> dict[str, Any]:
    identity = identity_from_request(request)
    if identity is None:
        raise HTTPException(status_code=401, detail="A lender session token is required")
    if identity.get("role") != "lender":
        raise HTTPException(status_code=403, detail="Merchant sessions cannot access lender endpoints")
    return identity


def require_merchant(request: Request) -> dict[str, Any]:
    identity = identity_from_request(request)
    if identity is None:
        raise HTTPException(status_code=401, detail="A merchant session token is required")
    if identity.get("role") != "merchant":
        raise HTTPException(status_code=403, detail="Lender sessions cannot access merchant-only endpoints")
    return identity
