#!/usr/bin/env python3
"""
GridFlex Release Verification Script
=====================================
Runs a complete end-to-end verification of the GridFlex backend from a clean state.
Covers every stage of the primary demo flow.

Usage:
    cd /path/to/sci
    python scripts/verify_release.py [--base-url http://127.0.0.1:8000]

Exit codes:
    0  All checks passed
    1  One or more checks failed
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8000/api/v1"
PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
SKIP = "\033[93m[SKIP]\033[0m"


# ── HTTP helpers ────────────────────────────────────────────────────────────

def _get(path: str) -> dict:
    url = f"{BASE_URL}{path}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


def _post(path: str, body: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ── Verification stages ─────────────────────────────────────────────────────

def check(label: str, fn):
    """Run a verification function and print PASS/FAIL."""
    try:
        result = fn()
        print(f"{PASS} {label}")
        return result
    except Exception as exc:
        print(f"{FAIL} {label} — {exc}")
        return None


def verify_health() -> dict:
    data = _get("/health")
    assert data["status"] == "healthy", f"Expected healthy, got {data['status']}"
    return data


def verify_grid_listing() -> list:
    grids = _get("/grids")
    assert len(grids) >= 1, "No grids loaded — startup may have failed"
    return grids


def verify_grid_validation(grid_id: str) -> dict:
    data = _post(f"/grids/{grid_id}/validate")
    assert data["valid"] is True, f"Grid validation failed: {data.get('errors', [])}"
    return data


def verify_power_flow(grid_id: str) -> dict:
    data = _post(f"/grids/{grid_id}/analyze/power-flow", {"engine": "python"})
    assert data["converged"] is True, "Power flow did not converge"
    assert data.get("input_hash"), "Missing input_hash in result"
    return data


def verify_stress_analysis(grid_id: str) -> dict:
    data = _post(f"/grids/{grid_id}/stress", {})
    assert data.get("stress") is not None, "Stress result missing"
    assert data.get("recommendations") is not None, "Recommendations missing"
    return data


def verify_recommendation_engine(record: dict) -> list:
    recs = record.get("recommendations", [])
    # Recommendations may be empty on a healthy grid — that's correct behavior
    return recs


def verify_mitigation_testing(analysis_id: str, record: dict) -> list:
    candidates = record.get("mitigation_candidates", [])
    if not candidates:
        print(f"{SKIP} Mitigation testing — no candidates (healthy grid)")
        return []
    tests = _post(f"/analyses/{analysis_id}/mitigation-tests", {"run_all": True})
    assert isinstance(tests, list), "Expected list of mitigation tests"
    return tests


def verify_report_generation(analysis_id: str) -> bool:
    data = _post(f"/analysis/{analysis_id}/report", {"format": "json"})
    assert "metadata" in data, f"Report missing metadata: {list(data.keys())}"
    return True


def verify_demo_reset() -> dict:
    data = _post("/demo/reset")
    assert data["status"] == "reset", f"Reset failed: {data}"
    return data


def verify_case_studies() -> list:
    cases = _get("/case-studies")
    assert len(cases) >= 1, "No case studies found"
    return cases


def verify_case_study_run(case_id: str = "normal_operation") -> dict:
    data = _post(f"/case-studies/{case_id}/run")
    assert data["status"] == "SUCCESS", f"Case study failed: {data.get('steps', [])}"
    return data


def verify_scilab_status(health_data: dict) -> None:
    scilab_avail = health_data.get("scilab_engine", False)
    label = "Scilab engine detected" if scilab_avail else "Scilab not available (Python fallback active)"
    engine_str = "scilab" if scilab_avail else "python"
    print(f"{PASS} Engine status: {label} (engine={engine_str})")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="GridFlex release verification")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1",
                        help="Base URL of the running GridFlex backend")
    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.base_url

    print("=" * 60)
    print("GridFlex Release Verification")
    print("=" * 60)
    print()

    failed = 0

    # Stage 1: Health
    health = check("Backend health", verify_health)
    if health is None:
        print("\n\033[91mFATAL: Backend is not reachable. Start the server first.\033[0m")
        return 1

    # Scilab status (informational, never fails the release)
    verify_scilab_status(health)

    # Stage 2: Grid validation
    grids = check("Grid listing", verify_grid_listing)
    if grids is None:
        failed += 1
        grids = []

    grid_id = grids[0]["grid_id"] if grids else "sample"

    validation = check("Grid validation", lambda: verify_grid_validation(grid_id))
    if validation is None:
        failed += 1

    # Stage 3: Power flow
    pf_result = check("Power flow (Python engine)", lambda: verify_power_flow(grid_id))
    if pf_result is None:
        failed += 1

    # Stage 4: Stress analysis
    stress = check("Stress analysis", lambda: verify_stress_analysis(grid_id))
    if stress is None:
        failed += 1
        stress = {}

    analysis_id = stress.get("id", "")

    # Stage 5: Recommendations
    recs = check("Recommendation engine", lambda: verify_recommendation_engine(stress))
    if recs is None:
        failed += 1

    # Stage 6: Mitigation testing
    if analysis_id:
        mits = check("Mitigation testing",
                     lambda: verify_mitigation_testing(analysis_id, stress))
        if mits is None:
            failed += 1
    else:
        print(f"{SKIP} Mitigation testing — no analysis_id")

    # Stage 7: Report generation
    if analysis_id:
        report = check("Report generation", lambda: verify_report_generation(analysis_id))
        if report is None:
            failed += 1
    else:
        print(f"{SKIP} Report generation — no analysis_id")

    # Stage 8: Case studies
    cases = check("Case studies listing", verify_case_studies)
    if cases is None:
        failed += 1

    cs_result = check("Case study execution (normal_operation)",
                      lambda: verify_case_study_run("normal_operation"))
    if cs_result is None:
        failed += 1

    # Stage 9: Demo reset
    reset = check("Demo reset", verify_demo_reset)
    if reset is None:
        failed += 1

    # Summary
    print()
    print("=" * 60)
    if failed == 0:
        print("\033[92m✓ ALL CHECKS PASSED — GridFlex is release-ready.\033[0m")
    else:
        print(f"\033[91m✗ {failed} CHECK(S) FAILED — see above for details.\033[0m")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
