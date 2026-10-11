from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import Alert, Merchant
from app.services.alerts import merchant_signal_evaluation


def lender_headers():
    client = TestClient(app)
    token = client.post("/auth/lender/verify-otp", json={"phone": "+919900000099", "code": "123456"}).json()["session_token"]
    return client, {"Authorization": f"Bearer {token}"}


def test_seeded_scenarios_and_consent_filtering():
    db = SessionLocal()
    try:
        by_id = {merchant.id: merchant for merchant in db.query(Merchant).all()}
        assert merchant_signal_evaluation(db, by_id[8])["signals"]["signals"][0]["severity"] == "red"
        assert merchant_signal_evaluation(db, by_id[2])["signals"]["status"] == "green"
        assert next(signal for signal in merchant_signal_evaluation(db, by_id[11])["signals"]["signals"] if signal["id"] == "S4")["severity"] == "red"
    finally:
        db.close()
    client, headers = lender_headers()
    portfolio = client.get("/lender/portfolio", headers=headers)
    assert portfolio.status_code == 200
    body = portfolio.json()
    assert len(body["merchants"]) == 12
    revoked = next(item for item in body["merchants"] if item["id"] == 12)
    assert revoked["id"] == 12
    assert revoked["priority"] == "consent withdrawn"
    assert revoked["days_until_due"] is None
    assert revoked["status"] == "consent withdrawn"
    assert revoked["consent_status"] == "revoked"
    detail = client.get("/lender/merchants/12", headers=headers)
    assert detail.status_code == 200
    assert "weekly" not in detail.json()
    merchant_token = client.post("/auth/verify-otp", json={"phone": "+919900000001", "code": "123456"}).json()["session_token"]
    assert client.get("/lender/portfolio", headers={"Authorization": f"Bearer {merchant_token}"}).status_code == 403


def test_alert_evaluation_is_idempotent():
    client, headers = lender_headers()
    first = client.post("/lender/evaluate?as_of=2026-09-30", headers=headers).json()
    second = client.post("/lender/evaluate?as_of=2026-09-30", headers=headers).json()
    assert first["alerts"] == second["alerts"]
