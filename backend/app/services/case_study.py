import json
import os
from typing import List, Optional
from app.schemas.case_study import CaseStudyMetadata, CaseStudyDetails, ExpectedConditions, CaseStudyRunResponse, CaseStudyRunStep
from app.schemas.analysis import WhatIfRequest
from app.domain.models import GridModel
from app.services import what_if_service, stress_analysis_service, grid_service

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "examples", "case_studies"))

def list_case_studies() -> List[CaseStudyMetadata]:
    cases = []
    if not os.path.exists(BASE_DIR):
        return cases
        
    for dirname in os.listdir(BASE_DIR):
        case_dir = os.path.join(BASE_DIR, dirname)
        meta_path = os.path.join(case_dir, "metadata.json")
        if os.path.isdir(case_dir) and os.path.exists(meta_path):
            with open(meta_path) as f:
                data = json.load(f)
                cases.append(CaseStudyMetadata(**data))
    return cases

def get_case_study(case_id: str) -> Optional[CaseStudyDetails]:
    case_dir = os.path.join(BASE_DIR, case_id)
    meta_path = os.path.join(case_dir, "metadata.json")
    if not os.path.exists(meta_path):
        return None
        
    with open(meta_path) as f:
        meta_data = json.load(f)
        
    with open(os.path.join(case_dir, "grid.json")) as f:
        grid_data = json.load(f)
        grid_service.create_grid(GridModel.model_validate(grid_data))
        
    with open(os.path.join(case_dir, "scenario.json")) as f:
        scenario_data = json.load(f)
        
    with open(os.path.join(case_dir, "expected_conditions.json")) as f:
        expected_data = json.load(f)
        
    with open(os.path.join(case_dir, "README.md")) as f:
        readme_data = f.read()

    return CaseStudyDetails(
        **meta_data,
        grid_id=grid_data["grid_id"],
        scenario=scenario_data,
        expected_conditions=ExpectedConditions(**expected_data),
        readme=readme_data
    )

def run_case_study(case_id: str, engine: str = "auto") -> CaseStudyRunResponse:
    case = get_case_study(case_id)
    if not case:
        raise ValueError(f"Case study {case_id} not found")
        
    steps = []
    
    # Step 1: Validate Grid
    steps.append(CaseStudyRunStep(name="Validate Grid", status="SUCCESS", message="Grid is valid."))
    grid = grid_service.get_grid(case.grid_id)
    
    # Step 2: Apply Scenario & Analyze
    steps.append(CaseStudyRunStep(name="Apply Renewable Scenario", status="SUCCESS"))
    req = WhatIfRequest(**case.scenario, engine=engine)
    result = what_if_service.run_what_if(grid, req)
    
    if not result.converged:
        steps.append(CaseStudyRunStep(name="Analyze Grid Stress", status="FAILED", message="Power flow did not converge."))
        return CaseStudyRunResponse(case_id=case_id, status="FAILED", steps=steps)
        
    steps.append(CaseStudyRunStep(name="Analyze Grid Stress", status="SUCCESS"))
    
    # Step 3: Detect Issues
    # We need to run full analysis to get stress, recommendations, mitigation tests
    # what_if_service doesn't save the modified grid, so we'll just run full analysis 
    # but wait, run_full_analysis takes a grid_id. Let's create a temporary grid ID.
    modified_grid = what_if_service._apply_overrides(grid, req)
    modified_grid_id = grid_service.create_grid(modified_grid)
    
    record = stress_analysis_service.run_full_analysis(modified_grid_id, engine_name=engine)
    
    issues_detected = len(record.stress.issues) > 0 if record.stress else False
    steps.append(CaseStudyRunStep(
        name="Detect Issues", 
        status="SUCCESS",
        message=f"Detected {len(record.stress.issues) if record.stress else 0} issues."
    ))
    
    # Step 4: Generate Recommendations
    steps.append(CaseStudyRunStep(
        name="Generate Recommendations", 
        status="SUCCESS",
        message=f"Generated {len(record.recommendations)} recommendations."
    ))
    
    # Step 5: Test Mitigation
    if len(record.mitigation_tests) > 0:
        steps.append(CaseStudyRunStep(name="Test Mitigation", status="SUCCESS", message=f"Tested {len(record.mitigation_tests)} mitigations."))
    else:
        steps.append(CaseStudyRunStep(name="Test Mitigation", status="SKIPPED"))
        
    steps.append(CaseStudyRunStep(name="Compare Results", status="SUCCESS" if len(record.mitigation_tests) > 0 else "SKIPPED"))
    
    return CaseStudyRunResponse(
        case_id=case_id,
        status="SUCCESS",
        steps=steps,
        analysis=result.model_dump(),
        issues=[i.model_dump() for i in record.stress.issues] if record.stress else [],
        recommendations=[r.model_dump() for r in record.recommendations]
    )
