"""Canonical signed records and a tamper-evident hash chain."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from eth_account import Account
from eth_account.messages import encode_defunct
from sqlalchemy.orm import Session

from ..config import settings
from ..models import AuditRecord

try:
    from eth_hash.auto import keccak
except Exception:  # pragma: no cover - exercised only in minimal installations
    keccak = None


def _normalise(value: Any) -> Any:
    """Make JSON deterministic, including fixed two-place decimal strings."""

    if isinstance(value, Decimal):
        return format(value.quantize(Decimal("0.01")), "f")
    if isinstance(value, float):
        try:
            return format(Decimal(str(value)).quantize(Decimal("0.01")), "f")
        except InvalidOperation:
            return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {str(key): _normalise(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_normalise(item) for item in value]
    return value


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(_normalise(record), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_canonical(canonical: str) -> str:
    data = canonical.encode("utf-8")
    digest = keccak(data) if keccak is not None else hashlib.sha256(data).digest()
    return "0x" + digest.hex()


def _signer() -> Account:
    return Account.from_key(settings.signing_key)


def sign_hash(record_hash: str) -> str:
    signed = _signer().sign_message(encode_defunct(hexstr=record_hash))
    return signed.signature.hex()


def verify_signature(record_hash: str, signature: str) -> bool:
    try:
        recovered = Account.recover_message(encode_defunct(hexstr=record_hash), signature=signature)
        return recovered.lower() == _signer().address.lower()
    except Exception:
        return False


def canonical_record_from_json(record_json: str) -> str:
    return canonical_json(json.loads(record_json))


def create_audit_record(
    db: Session,
    *,
    loan_id: int,
    record_type: str,
    record: dict[str, Any],
    rule_version: str,
) -> AuditRecord:
    previous = db.query(AuditRecord).order_by(AuditRecord.id.desc()).first()
    canonical = canonical_json(record)
    record_hash = hash_canonical(canonical)
    audit = AuditRecord(
        loan_id=loan_id,
        record_type=record_type,
        record_json=canonical,
        record_hash=record_hash,
        signature=sign_hash(record_hash),
        prev_hash=previous.record_hash if previous else None,
        rule_version=rule_version,
    )
    db.add(audit)
    db.flush()
    return audit


def _verify_chain(db: Session, target: AuditRecord) -> bool:
    expected_previous: str | None = None
    records = db.query(AuditRecord).filter(AuditRecord.id <= target.id).order_by(AuditRecord.id).all()
    for item in records:
        try:
            recomputed = hash_canonical(item.record_json)
        except (TypeError, ValueError, json.JSONDecodeError):
            return False
        if recomputed != item.record_hash or item.prev_hash != expected_previous:
            return False
        expected_previous = item.record_hash
    return bool(records and records[-1].id == target.id)


def verify_audit_record(db: Session, audit: AuditRecord) -> dict[str, Any]:
    try:
        recomputed_hash = hash_canonical(audit.record_json)
    except (TypeError, ValueError, json.JSONDecodeError):
        recomputed_hash = ""
    hash_valid = recomputed_hash == audit.record_hash
    signature_valid = verify_signature(audit.record_hash, audit.signature)
    chain_valid = _verify_chain(db, audit)
    anchored = audit.anchored_tx_hash is not None
    verified = hash_valid and signature_valid and chain_valid
    return {
        "verified": verified,
        "hash_valid": hash_valid,
        "signature_valid": signature_valid,
        "chain_valid": chain_valid,
        "anchored": anchored,
        "message": (
            "This record is verified: its contents, signature, and chain link match."
            if verified
            else "This record could not be verified: its contents, signature, or chain link did not match."
        ),
    }
