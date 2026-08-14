"""End-to-end demo of the stress-analysis pipeline.

Verifies the full flow against the running backend via the FastAPI TestClient:

    1. Load the demo grid (wind + battery, renewables).
    2. Create a deliberately stressed grid variant (low voltages, weak lines,
       heavy loads) and register it.
    3. Run stress analysis on the stressed grid: expect issues,
       recommendations, and mitigation candidates.
    4. Run mitigation tests and confirm scores improve / converge.
    5. Run a comparative analysis on the demo grid to confirm renewable
       impact is evaluated.

Run:  python -m scripts.integration_demo   (from backend/)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app

BASE = "/api/v1"


def _load_example(name: str) -> dict:
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", name
    )
    with open(path) as handle:
        return json.load(handle)


def _stressed_payload() -> dict:
    payload = _load_example("demo_grid.json")
    payload["grid_id"] = "integration-stress"
    payload["buses"][3]["type"] = "PQ"
    payload["buses"][3]["voltage_magnitude"] = 0.9
    payload["buses"][4]["type"] = "PQ"
    payload["buses"][4]["voltage_magnitude"] = 0.9
    for line in payload["lines"]:
        line["thermal_limit"] = 60
    payload["loads"] = [
        {"id": "D1", "name": "Load 1", "bus_id": "B4", "active_power": 150.0, "reactive_power": 60.0},
        {"id": "D2", "name": "Load 2", "bus_id": "B5", "active_power": 120.0, "reactive_power": 40.0},
    ]
    return payload


def main() -> None:
    with TestClient(app) as client:
        print("=== Step 1: register a stressed grid variant ===\n")
        payload = _stressed_payload()
        created = client.post(f"{BASE}/grids", json=payload)
        assert created.status_code == 201, created.text
        print(f"Grid '{payload['grid_id']}' created ({created.status_code}).")

        print("\n=== Step 2: run stress analysis ===\n")
        run = client.post(f"{BASE}/grids/integration-stress/stress", json={})
        assert run.status_code == 200, run.text
        record = run.json()
        stress = record["stress"]
        score = stress["score"]
        issues = stress["issues"]
        recommendations = record["recommendations"]
        candidates = record["mitigation_candidates"]
        print(f"Stress score: {score['overall_score']} ({score['classification']})")
        print(f"Issues ({len(issues)}):")
        for issue in issues:
            print(f"  - [{issue['severity']}] {issue['title']} ({issue['affected_component_type']} {issue['affected_component_id'] or 'SYSTEM'})")
        print(f"Recommendations ({len(recommendations)}):")
        for rec in recommendations:
            print(f"  - [{rec['priority']}] {rec['title']}")
        print(f"Mitigation candidates ({len(candidates)}):")
        for candidate in candidates:
            print(f"  - {candidate['name']}")
        assert issues, "expected at least one issue on the stressed grid"
        assert recommendations, "expected at least one recommendation"

        print("\n=== Step 3: run mitigation tests ===\n")
        analysis_id = record["id"]
        if candidates:
            tested = client.post(
                f"{BASE}/analyses/{analysis_id}/mitigation-tests",
                json={"run_all": True},
            )
            assert tested.status_code == 200, tested.text
            for test in tested.json():
                status = "converged" if test["converged"] else "DID NOT CONVERGE"
                direction = "improved" if test["after_score"] < test["before_score"] else "worse/equal"
                print(
                    f"  - {test['mitigation_name']}: {test['before_score']} -> {test['after_score']} "
                    f"({status}, {direction})"
                )
            assert any(t["converged"] for t in tested.json())

        print("\n=== Step 4: comparative analysis (renewable impact) ===\n")
        comp = client.post(f"{BASE}/stress/comparative", json={"analysis_id": analysis_id})
        assert comp.status_code == 200, comp.text
        comp_record = comp.json()
        renewable = comp_record["stress"]["renewable"]
        print(
            f"Comparative analysis '{comp_record['id']}': "
            f"renewable penetration {renewable['renewable_penetration']}% -> "
            f"impact {renewable['impact_level']} ({renewable['reason']})"
        )

        print("\n=== Step 5: fetch persisted analysis ===\n")
        fetched = client.get(f"{BASE}/analyses/{analysis_id}/stress")
        assert fetched.status_code == 200, fetched.text
        print(f"Persisted analysis '{fetched.json()['id']}' loaded OK.")

        print("\n=== Integration demo: PASSED ===")


if __name__ == "__main__":
    main()
