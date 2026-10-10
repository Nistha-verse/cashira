from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import AuditRecord
from app.services.audit import canonical_json, create_audit_record, verify_audit_record


def test_canonical_record_is_sorted_and_fixed():
    assert canonical_json({"b": 2.5, "a": "first"}) == '{"a":"first","b":"2.50"}'


def test_audit_chain_and_tamper_detection():
    db: Session = SessionLocal()
    try:
        db.query(AuditRecord).delete()
        db.commit()
        first = create_audit_record(
            db, loan_id=1, record_type="recommendation", record={"event": "recommendation", "emi": 1200.0}, rule_version="test-v1"
        )
        second = create_audit_record(
            db, loan_id=1, record_type="payment", record={"event": "payment", "amount": 1200.0}, rule_version="test-v1"
        )
        db.commit()
        assert verify_audit_record(db, first)["verified"] is True
        assert verify_audit_record(db, second)["chain_valid"] is True
        first.record_json = '{"emi":"9999.00","event":"recommendation"}'
        db.commit()
        result = verify_audit_record(db, first)
        assert result["verified"] is False
        assert result["hash_valid"] is False
        assert verify_audit_record(db, second)["chain_valid"] is False
    finally:
        db.close()
