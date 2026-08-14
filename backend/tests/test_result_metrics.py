import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

SAMPLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "examples",
    "sample_grid.json",
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_payload() -> dict:
    with open(SAMPLE_PATH) as handle:
        return json.load(handle)


def test_result_includes_new_metrics(client):
    response = client.post("/api/v1/grids/sample/analyze/power-flow", json={})
    body = response.json()
    assert body["converged"] is True
    assert body["execution_time_ms"] > 0
    summary = body["summary"]
    assert summary["renewable_generation_mw"] == 40.0
    assert summary["maximum_line_loading"] > 0
    assert summary["overloaded_lines"] == 0
    assert "total_generation_mw" in summary
    impact = body["impact_score"]
    assert 0 <= impact["score"] <= 100
    assert impact["grade"] in {"A", "B", "C", "D", "F"}
    assert set(impact["categories"]) == {"voltage", "loading", "losses"}
    assert impact["message"]


def test_put_updates_grid(client, sample_payload):
    payload = json.loads(json.dumps(sample_payload))
    payload["generators"][2]["active_power"] = 70.0
    response = client.put("/api/v1/grids/sample", json=payload)
    assert response.status_code == 200
    assert response.json()["generators"][2]["active_power"] == 70.0

    fetched = client.get("/api/v1/grids/sample")
    assert fetched.json()["generators"][2]["active_power"] == 70.0

    restored = client.put("/api/v1/grids/sample", json=sample_payload)
    assert restored.status_code == 200


def test_put_missing_grid(client, sample_payload):
    response = client.put("/api/v1/grids/nope", json=sample_payload)
    assert response.status_code == 404


def test_battery_model_roundtrip(client, sample_payload):
    payload = json.loads(json.dumps(sample_payload))
    battery = {
        "id": "G4",
        "name": "Battery",
        "bus_id": "B5",
        "type": "STORAGE",
        "active_power": 0.0,
        "reactive_power": 0.0,
        "active_power_min": -50,
        "active_power_max": 50,
        "reactive_power_min": -25,
        "reactive_power_max": 25,
        "capacity_mwh": 100,
    }
    payload["generators"].append(battery)
    payload["grid_id"] = "with-battery"
    created = client.post("/api/v1/grids", json=payload)
    assert created.status_code == 201
    stored = created.json()["generators"][-1]
    assert stored["type"] == "STORAGE"
    assert stored["capacity_mwh"] == 100.0

    analyzed = client.post("/api/v1/grids/with-battery/analyze/power-flow", json={})
    assert analyzed.status_code == 200
    assert analyzed.json()["converged"] is True


def test_demo_grid_preloaded(client):
    response = client.get("/api/v1/grids/demo")
    assert response.status_code == 200
    types = {gen["type"] for gen in response.json()["generators"]}
    assert types == {"CONVENTIONAL", "SOLAR", "WIND", "STORAGE"}
