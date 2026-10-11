from fastapi.testclient import TestClient

from app.main import app


def test_merchant_and_lender_tokens_have_separate_roles():
    client = TestClient(app)
    merchant = client.post("/auth/verify-otp", json={"phone": "+919900000001", "code": "123456"}).json()
    lender = client.post("/auth/lender/verify-otp", json={"phone": "+919900000099", "code": "123456"}).json()
    assert merchant["role"] == "merchant"
    assert lender["role"] == "lender"
    assert merchant["merchant_id"] == 1
    assert lender["lender_id"] == 1


def test_merchant_consent_endpoint_returns_active_record():
    client = TestClient(app)
    token = client.post("/auth/verify-otp", json={"phone": "+919900000001", "code": "123456"}).json()["session_token"]
    response = client.get("/merchant/consent", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["consent"]["status"] == "active"
    assert response.json()["consent"]["scope"] == "transaction history"
