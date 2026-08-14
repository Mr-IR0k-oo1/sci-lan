import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

def run_smoke_test():
    print("Running Smoke Test...")
    
    with TestClient(app) as client:
        print("1. Testing Health Endpoint")
        resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    print("   [PASS]")
    
    print("2. Testing Engine Status")
    resp = client.get("/api/v1/engines")
    assert resp.status_code == 200
    print("   [PASS]")
    
    print("3. Testing Grid Listing")
    resp = client.get("/api/v1/grids")
    assert resp.status_code == 200
    grids = resp.json()
    assert len(grids) > 0
    grid_id = grids[0]["grid_id"]
    print(f"   [PASS] Found grid {grid_id}")
    
    print("4. Testing Power Flow")
    resp = client.post(f"/api/v1/grids/{grid_id}/analyze/power-flow", json={"engine": "python"})
    assert resp.status_code == 200
    pf_result = resp.json()
    assert pf_result["converged"] is True
    analysis_id = pf_result.get("analysis_id")
    print(f"   [PASS] Converged. Analysis ID: {analysis_id}")
    
    print("5. Testing Case Studies List")
    resp = client.get("/api/v1/case-studies")
    assert resp.status_code == 200
    cases = resp.json()
    assert len(cases) >= 5
    print(f"   [PASS] Found {len(cases)} cases")
    
    print("6. Testing Run Case Study")
    case_id = cases[0]["id"]
    resp = client.post(f"/api/v1/case-studies/{case_id}/run")
    assert resp.status_code == 200
    run_result = resp.json()
    assert run_result["status"] == "SUCCESS"
    print("   [PASS]")

    print("\nALL STAGES PASSED.")
    return 0
    
if __name__ == "__main__":
    try:
        sys.exit(run_smoke_test())
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        sys.exit(1)
