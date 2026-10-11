from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_payments_are_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "payments_enabled", False)
    client = TestClient(app)
    token = client.post("/auth/verify-otp", json={"phone": "+919900000001", "code": "123456"}).json()["session_token"]
    result = client.post("/loan/pay", headers={"Authorization": f"Bearer {token}"}, json={})
    assert result.status_code == 403
    assert "disabled" in result.json()["error"]


def test_lender_alert_action_changes_status():
    client = TestClient(app)
    token = client.post("/auth/lender/verify-otp", json={"phone": "+919900000099", "code": "123456"}).json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/lender/evaluate?as_of=2026-09-30", headers=headers)
    alert_id = client.get("/lender/alerts?severity=red", headers=headers).json()["alerts"][0]["id"]
    result = client.post(f"/lender/alerts/{alert_id}/acknowledge", headers=headers)
    assert result.status_code == 200
    assert result.json()["status"] == "acknowledged"
