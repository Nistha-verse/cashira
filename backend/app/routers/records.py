from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuditRecord
from ..schemas import VerifyRequest
from ..services.audit import verify_audit_record
from .helpers import iso_datetime, response

router = APIRouter(prefix="/records", tags=["records"])


def receipt_payload(audit: AuditRecord) -> dict:
    return {
        "id": audit.id,
        "record_type": audit.record_type,
        "record": json.loads(audit.record_json),
        "hash": audit.record_hash,
        "signature": audit.signature,
        "prev_hash": audit.prev_hash,
        "rule_version": audit.rule_version,
        "created_at": iso_datetime(audit.created_at),
        "anchored_tx_hash": audit.anchored_tx_hash,
    }


@router.get("/{record_id}/receipt")
def record_receipt(record_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    audit = db.get(AuditRecord, record_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="Record not found")
    body = response({"record": receipt_payload(audit)})
    return JSONResponse(
        content=body,
        headers={"Content-Disposition": f'attachment; filename="cashira-record-{record_id}.json"'},
    )


@router.post("/verify")
def verify_record(payload: VerifyRequest, db: Session = Depends(get_db)) -> dict:
    audit = db.get(AuditRecord, payload.record_id) if payload.record_id else None
    if audit is None and payload.record:
        supplied_hash = payload.hash
        supplied_signature = payload.signature
        if not supplied_hash or not supplied_signature:
            raise HTTPException(status_code=422, detail="record, hash, and signature are required")
        from ..services.audit import canonical_json, hash_canonical, verify_signature

        recomputed = hash_canonical(canonical_json(payload.record))
        hash_valid = recomputed == supplied_hash
        signature_valid = verify_signature(supplied_hash, supplied_signature)
        verified = hash_valid and signature_valid
        return response(
            {
                "verified": verified,
                "hash_valid": hash_valid,
                "signature_valid": signature_valid,
                "chain_valid": False,
                "anchored": False,
                "message": "The supplied record is cryptographically verified." if verified else "The supplied record could not be verified.",
            }
        )
    if audit is None:
        raise HTTPException(status_code=404, detail="Record not found; provide record_id or a complete receipt")
    return response(verify_audit_record(db, audit))
