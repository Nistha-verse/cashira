from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_demo_controls_require_flag_and_can_reset(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(settings, "demo_mode", False)
    denied = client.post("/demo/simulate-week", json={"merchant_id": 2, "pattern": "decline"})
    assert denied.status_code == 403
    monkeypatch.setattr(settings, "demo_mode", True)
    simulated = client.post("/demo/simulate-week", json={"merchant_id": 2, "pattern": "decline"})
    assert simulated.status_code == 200
    assert simulated.json()["demo_only"] is True
    reset = client.post("/demo/reset")
    assert reset.status_code == 200
    assert reset.json()["seed"]["merchants"] == 12
