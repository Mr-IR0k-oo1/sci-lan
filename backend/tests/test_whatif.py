import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402
from app.services import grid_service  # noqa: E402

DEMO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "examples",
    "demo_grid.json",
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def demo_payload() -> dict:
    with open(DEMO_PATH) as handle:
        return json.load(handle)


def _solar_output(payload: dict) -> float:
    return next(g for g in payload["generators"] if g["id"] == "G3")["active_power"]


def test_what_if_solar_override(client):
    response = client.post(
        "/api/v1/grids/demo/what-if",
        json={"solar_output_mw": 75},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["converged"] is True
    assert body["summary"]["renewable_generation_mw"] == pytest.approx(95.0)


def test_what_if_load_scale(client):
    response = client.post(
        "/api/v1/grids/demo/what-if",
        json={"load_scale": 1.2},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total_load_mw"] == pytest.approx(115.0 * 1.2)


def test_what_if_battery_discharge(client):
    response = client.post(
        "/api/v1/grids/demo/what-if",
        json={"battery_output_mw": 40},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["renewable_generation_mw"] == pytest.approx(60.0)
    assert body["summary"]["total_generation_mw"] == pytest.approx(160.0, abs=1.0)


def test_what_if_is_temporary_and_base_unchanged(client, demo_payload):
    base_before = grid_service.get_grid("demo")
    client.post("/api/v1/grids/demo/what-if", json={"solar_output_mw": 95, "load_scale": 1.5})
    client.post("/api/v1/grids/demo/what-if", json={"battery_output_mw": 45})
    base_after = grid_service.get_grid("demo")
    assert base_after == base_before
    assert _solar_output(base_after.model_dump()) == 40.0


def test_what_if_full_grid_override(client, demo_payload):
    payload = json.loads(json.dumps(demo_payload))
    payload["generators"][2]["active_power"] = 60.0
    response = client.post(
        "/api/v1/grids/demo/what-if",
        json={"grid": payload},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["renewable_generation_mw"] == pytest.approx(80.0)


def test_what_if_invalid_grid_rejected(client, demo_payload):
    payload = json.loads(json.dumps(demo_payload))
    payload["buses"][0]["type"] = "PQ"
    response = client.post(
        "/api/v1/grids/demo/what-if",
        json={"grid": payload},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_grid"


def test_what_if_missing_grid(client):
    response = client.post("/api/v1/grids/nope/what-if", json={"solar_output_mw": 50})
    assert response.status_code == 404
