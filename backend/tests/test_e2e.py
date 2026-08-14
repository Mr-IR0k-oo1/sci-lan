import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_health():
    with TestClient(app) as client:
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

def test_case_studies_exist():
    with TestClient(app) as client:
        resp = client.get("/api/v1/case-studies")
        assert resp.status_code == 200
        cases = resp.json()
        assert len(cases) >= 5

def test_run_normal_case():
    with TestClient(app) as client:
        resp = client.post("/api/v1/case-studies/normal_operation/run")
        assert resp.status_code == 200
        res = resp.json()
        assert res["status"] == "SUCCESS"
        assert "analysis" in res

def test_run_over_voltage_case():
    with TestClient(app) as client:
        resp = client.post("/api/v1/case-studies/over_voltage/run")
        assert resp.status_code == 200
        res = resp.json()
        assert res["status"] == "SUCCESS"
        assert "issues" in res

def test_run_line_overload_case():
    with TestClient(app) as client:
        resp = client.post("/api/v1/case-studies/line_overload/run")
        assert resp.status_code == 200
        res = resp.json()
        assert res["status"] == "SUCCESS"
        assert "issues" in res

def test_power_flow_reproducibility():
    with TestClient(app) as client:
        resp1 = client.post("/api/v1/case-studies/normal_operation/run")
        resp2 = client.post("/api/v1/case-studies/normal_operation/run")
        
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        
        analysis1 = resp1.json()["analysis"]
        analysis2 = resp2.json()["analysis"]
        
        assert analysis1["input_hash"] == analysis2["input_hash"]

