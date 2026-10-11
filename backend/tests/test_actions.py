from fastapi.testclient import TestClient

from app.main import app


def test_lender_action_is_logged_and_message_is_localized():
    client = TestClient(app)
    token = client.post("/auth/lender/verify-otp", json={"phone": "+919900000099", "code": "123456"}).json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}
    action = client.post("/lender/merchants/4/actions", headers=headers, json={"type": "reminder", "note": "Please review", "lang": "bn"})
    assert action.status_code == 200
    body = action.json()
    assert body["sent"] is False
    assert body["language"] == "bn"
    assert body["audit_record_id"]
    listed = client.get("/lender/merchants/4/actions", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["actions"][0]["text"] == body["text"]
    merchant_token = client.post("/auth/verify-otp", json={"phone": "+919900000004", "code": "123456"}).json()["session_token"]
    messages = client.get("/merchant/messages", headers={"Authorization": f"Bearer {merchant_token}"})
    assert messages.status_code == 200
    assert messages.json()["messages"][0]["language"] == "bn"
    assert client.post("/records/verify", json={"record_id": body["audit_record_id"]}).json()["verified"] is True
