import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
import api, service

c = TestClient(api.app)


def test_valid():
    r = c.post("/analyze", json={"ticket": "The printer in the library is out of toner."})
    assert r.status_code == 200 and r.json()["category"] == "printing"


def test_blank():
    assert c.post("/analyze", json={"ticket": "   "}).status_code == 400


def test_backend_down():
    assert c.post("/analyze", json={"ticket": "x", "simulate_failure": True}).status_code == 503


def test_invalid_model_output(monkeypatch):
    monkeypatch.setattr(service, "call_model", lambda t, v: '{"category": "refunds", "summary": "Ok."}')
    assert c.post("/analyze", json={"ticket": "hello"}).status_code == 502


def test_summary_claims_action(monkeypatch):
    monkeypatch.setattr(service, "call_model", lambda t, v: '{"category": "printing", "summary": "Printer has been fixed."}')
    assert c.post("/analyze", json={"ticket": "printer"}).status_code == 502
