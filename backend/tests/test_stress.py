import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

DEMO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "examples",
    "demo_grid.json",
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _load_demo() -> dict:
    with open(DEMO_PATH) as handle:
        return json.load(handle)


def _stressed_payload() -> dict:
    payload = _load_demo()
    payload["grid_id"] = "stress-test"
    payload["buses"][3]["type"] = "PQ"
    payload["buses"][3]["voltage_magnitude"] = 0.9
    payload["buses"][4]["type"] = "PQ"
    payload["buses"][4]["voltage_magnitude"] = 0.9
    for line in payload["lines"]:
        line["thermal_limit"] = 60
    payload["loads"] = [
        {
            "id": "D1",
            "name": "Load 1",
            "bus_id": "B4",
            "active_power": 150.0,
            "reactive_power": 60.0,
        },
        {
            "id": "D2",
            "name": "Load 2",
            "bus_id": "B5",
            "active_power": 120.0,
            "reactive_power": 40.0,
        },
    ]
    return payload


def test_stress_analysis_baseline(client):
    response = client.post("/api/v1/grids/demo/stress", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["id"]
    assert body["stress"] is not None
    assert body["stress"]["grid_id"] == "demo"
    assert body["stress"]["analysis_id"] == body["id"]
    assert "score" in body["stress"]
    assert "buses" in body["stress"]
    assert "lines" in body["stress"]
    assert "generation" in body["stress"]
    assert "renewable" in body["stress"]
    assert "issues" in body["stress"]
    assert isinstance(body["recommendations"], list)
    assert isinstance(body["mitigation_candidates"], list)


def test_stress_analysis_stressed_grid(client):
    payload = _stressed_payload()
    created = client.post("/api/v1/grids", json=payload)
    assert created.status_code == 201
    response = client.post("/api/v1/grids/stress-test/stress", json={})
    assert response.status_code == 200
    body = response.json()
    stress = body["stress"]
    issues = stress["issues"]
    assert len(issues) > 0
    titles = [issue["title"] for issue in issues]
    assert any("voltage" in title.lower() for title in titles) or any(
        "overload" in title.lower() for title in titles
    )
    assert stress["score"]["classification"] in {
        "LOW",
        "MODERATE",
        "HIGH",
        "CRITICAL",
    }


def test_stress_recommendations_follow_issues(client):
    payload = _stressed_payload()
    client.post("/api/v1/grids", json={**payload, "grid_id": "stress-test-2"})
    response = client.post("/api/v1/grids/stress-test-2/stress", json={})
    body = response.json()
    issue_titles = {issue["title"] for issue in body["stress"]["issues"]}
    rec_categories = {rec["category"] for rec in body["recommendations"]}
    if any("overvoltage" in title.lower() for title in issue_titles):
        assert "voltage" in rec_categories
    if any("overloaded" in title.lower() for title in issue_titles):
        assert "transmission" in rec_categories
    for rec in body["recommendations"]:
        assert rec["priority"] in {"LOW", "MEDIUM", "HIGH"}
        assert rec["confidence"] in {"LOW", "MEDIUM", "HIGH"}


def test_stress_get_analysis(client):
    created = client.post("/api/v1/grids/demo/stress", json={})
    analysis_id = created.json()["id"]
    response = client.get(f"/api/v1/analyses/{analysis_id}/stress")
    assert response.status_code == 200
    assert response.json()["id"] == analysis_id


def test_stress_get_missing_analysis(client):
    response = client.get("/api/v1/analyses/does-not-exist/stress")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "analysis_not_found"


def test_comparative_analysis(client):
    created = client.post("/api/v1/grids/demo/stress", json={})
    analysis_id = created.json()["id"]
    response = client.post(
        "/api/v1/stress/comparative", json={"analysis_id": analysis_id}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] != analysis_id
    assert body["stress"]["renewable"]["impact_level"] in {
        "POSITIVE",
        "NEUTRAL",
        "NEGATIVE",
        "HIGH_RISK",
    }


def test_mitigation_candidates_and_tests(client):
    payload = _stressed_payload()
    client.post("/api/v1/grids", json={**payload, "grid_id": "stress-test-3"})
    created = client.post("/api/v1/grids/stress-test-3/stress", json={})
    body = created.json()
    analysis_id = body["id"]
    candidates = client.get(f"/api/v1/analyses/{analysis_id}/mitigation-candidates")
    assert candidates.status_code == 200
    candidate_list = candidates.json()
    if candidate_list:
        tests = client.post(
            f"/api/v1/analyses/{analysis_id}/mitigation-tests",
            json={"run_all": True},
        )
        assert tests.status_code == 200
        for test in tests.json():
            assert test["analysis_id"] == analysis_id
            assert test["mitigation_id"]
            assert "before_score" in test
            assert "after_score" in test
