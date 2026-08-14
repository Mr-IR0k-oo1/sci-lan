import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402
from app.services import scenario_service  # noqa: E402

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


@pytest.fixture
def scenario_payload(sample_payload) -> dict:
    return {"name": "High Solar", "grid": sample_payload}


def test_create_list_analyze_delete_scenario(client, scenario_payload):
    created = client.post("/api/v1/grids/sample/scenarios", json=scenario_payload)
    assert created.status_code == 201
    scenario = created.json()
    assert scenario["name"] == "High Solar"
    assert scenario["id"]
    scenario_id = scenario["id"]

    listed = client.get("/api/v1/grids/sample/scenarios")
    assert listed.status_code == 200
    ids = [entry["id"] for entry in listed.json()]
    assert scenario_id in ids

    analyzed = client.post(
        f"/api/v1/grids/sample/scenarios/{scenario_id}/analyze",
        json={},
    )
    assert analyzed.status_code == 200
    body = analyzed.json()
    assert body["converged"] is True
    assert body["summary"]["total_load_mw"] == 115.0

    deleted = client.delete(f"/api/v1/grids/sample/scenarios/{scenario_id}")
    assert deleted.status_code == 204
    gone = client.get("/api/v1/grids/sample/scenarios")
    assert scenario_id not in [entry["id"] for entry in gone.json()]


def test_scenario_does_not_mutate_base_grid(client, sample_payload):
    modified = {**sample_payload}
    modified["generators"][2]["active_power"] = 90.0
    created = client.post(
        "/api/v1/grids/sample/scenarios",
        json={"name": "Solar 90", "grid": modified},
    )
    assert created.status_code == 201

    base = client.get("/api/v1/grids/sample").json()
    solar = next(g for g in base["generators"] if g["id"] == "G3")
    assert solar["active_power"] == 40.0


def test_run_missing_scenario(client):
    response = client.post(
        "/api/v1/grids/sample/scenarios/does-not-exist/analyze",
        json={},
    )
    assert response.status_code == 404


def test_delete_missing_scenario(client):
    response = client.delete("/api/v1/grids/sample/scenarios/does-not-exist")
    assert response.status_code == 404


def test_scenarios_for_missing_grid(client, scenario_payload):
    response = client.post("/api/v1/grids/nope/scenarios", json=scenario_payload)
    assert response.status_code == 404


def test_invalid_scenario_grid_rejected(client, scenario_payload):
    payload = scenario_payload["grid"]
    payload["buses"][0]["type"] = "PQ"
    created = client.post(
        "/api/v1/grids/sample/scenarios",
        json={"name": "Broken", "grid": payload},
    )
    scenario_id = created.json()["id"]
    response = client.post(
        f"/api/v1/grids/sample/scenarios/{scenario_id}/analyze",
        json={},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_grid"


def test_service_clear_scenarios():
    scenario_service.clear_scenarios()
    assert scenario_service.list_scenarios("sample") == []
