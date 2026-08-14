import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

SAMPLE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "sample_grid.json")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_payload() -> dict:
    with open(SAMPLE_PATH) as handle:
        return json.load(handle)


def test_engine_status(client):
    response = client.get("/api/v1/engines")
    assert response.status_code == 200
    payload = response.json()
    names = {engine["name"] for engine in payload["engines"]}
    assert names == {"python", "scilab"}
    by_name = {engine["name"]: engine for engine in payload["engines"]}
    assert by_name["python"]["available"] is True
    assert by_name["scilab"]["available"] is False
    assert payload["default_engine"] == "python"


def test_create_and_get_grid(client, sample_payload):
    payload = {**sample_payload, "grid_id": "test-create", "name": "Create Test"}
    response = client.post("/api/v1/grids", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["grid_id"] == "test-create"
    assert created["base_mva"] == 100.0
    assert len(created["buses"]) == 5

    fetched = client.get("/api/v1/grids/test-create")
    assert fetched.status_code == 200
    assert fetched.json()["grid_id"] == "test-create"


def test_get_missing_grid(client):
    response = client.get("/api/v1/grids/does-not-exist")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "grid_not_found"


def test_validate_valid_grid(client, sample_payload):
    payload = {**sample_payload, "grid_id": "test-validate-ok"}
    client.post("/api/v1/grids", json=payload)
    response = client.post("/api/v1/grids/test-validate-ok/validate")
    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["errors"] == []


def test_validate_invalid_grid(client, sample_payload):
    payload = {**sample_payload, "grid_id": "test-validate-bad"}
    payload["buses"][0]["type"] = "PQ"
    client.post("/api/v1/grids", json=payload)
    response = client.post("/api/v1/grids/test-validate-bad/validate")
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    codes = [issue["code"] for issue in body["errors"]]
    assert "missing_slack" in codes


def test_power_flow_on_sample(client):
    response = client.post("/api/v1/grids/sample/analyze/power-flow", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["converged"] is True
    assert body["status"] == "success"
    assert body["engine"] == "python"
    assert body["iterations"] >= 1
    assert len(body["buses"]) == 5
    assert len(body["lines"]) == 7
    assert body["summary"]["total_load_mw"] == 115.0
    assert body["summary"]["total_losses_mw"] > 0
    assert all("bus_id" in bus for bus in body["buses"])
    assert all("loading_percentage" in line for line in body["lines"])


def test_power_flow_structured_failure(client, sample_payload):
    payload = {**sample_payload, "grid_id": "test-noconv"}
    client.post("/api/v1/grids", json=payload)
    response = client.post(
        "/api/v1/grids/test-noconv/analyze/power-flow",
        json={"max_iterations": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["converged"] is False
    assert body["status"] == "not_converged"
    assert body["buses"] == []
    assert body["summary"] is None


def test_power_flow_rejects_invalid_grid(client, sample_payload):
    payload = {**sample_payload, "grid_id": "test-invalid-flow"}
    payload["buses"][0]["type"] = "PQ"
    client.post("/api/v1/grids", json=payload)
    response = client.post("/api/v1/grids/test-invalid-flow/analyze/power-flow", json={})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_grid"
    assert len(response.json()["detail"]["details"]) >= 1


def test_power_flow_missing_grid(client):
    response = client.post("/api/v1/grids/nope/analyze/power-flow", json={})
    assert response.status_code == 404


def test_invalid_engine_rejected(client):
    response = client.post(
        "/api/v1/grids/sample/analyze/power-flow",
        json={"engine": "nonexistent"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_engine"
