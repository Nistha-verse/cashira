from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_api_smoke_for_core_endpoints():
    paths = ["/health", "/merchant/me", "/merchant/transactions", "/merchant/summary", "/merchant/forecast", "/loan"]
    for path in paths:
        result = client.get(path)
        assert result.status_code == 200, (path, result.text)
        assert result.json()["prototype"] is True
    otp = client.post("/auth/request-otp", json={"phone": "+919900000001"})
    assert otp.status_code == 200
    verified = client.post("/auth/verify-otp", json={"phone": "+919900000001", "code": "123456"})
    assert verified.status_code == 200
    recommendation = client.get("/loan/recommendation")
    assert recommendation.status_code == 200
    body = recommendation.json()
    assert body["range"]["min"] <= body["current_emi"] <= body["range"]["max"]
    receipt = client.get(f"/records/{body['audit_record_id']}/receipt")
    assert receipt.status_code == 200
    assert receipt.headers["content-type"].startswith("application/json")
    assert client.post("/records/verify", json={"record_id": body["audit_record_id"]}).json()["verified"] is True
    payment = client.post("/loan/pay", json={})
    assert payment.status_code == 200
    assert payment.json()["payment"]["amount"] > 0
