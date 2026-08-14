from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from app.core.config import settings
from app.power_system.engines import build_registry
from app.power_system.results import PowerFlowResult
from app.schemas.analysis import (
    EngineComparisonRequest,
    EngineComparisonResponse,
    EngineRegistryResponse,
    PowerFlowRequest,
    ScilabStatusResponse,
    WhatIfRequest,
)
from app.scilab.capability import scilab_status_payload
from app.services import grid_service, power_flow_service, what_if_service
from app.services.engine_comparison_service import compare_engines
from app.services.fingerprint import compute_input_hash
from app.services.analysis_run_service import create_analysis_run
from app.services.analysis_history_service import get_analysis
from app.services.export_service import export_analysis

router = APIRouter(tags=["analysis"])

class ReportRequest(BaseModel):
    format: str = "markdown"

@router.post("/analysis/{analysis_id}/report")
def generate_report(analysis_id: str, request: ReportRequest):
    try:
        record = get_analysis(analysis_id)
        filename, content_type, body = export_analysis(record, fmt=request.format)
        
        if isinstance(body, dict):
            return body
            
        return Response(
            content=body,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/grids/{grid_id}/analyze/power-flow", response_model=PowerFlowResult)
def run_power_flow(grid_id: str, request: PowerFlowRequest) -> PowerFlowResult:
    grid = grid_service.get_grid(grid_id)
    input_hash = compute_input_hash(grid, engine=request.engine)
    result = power_flow_service.run_power_flow(
        grid,
        tolerance=request.tolerance,
        max_iterations=request.max_iterations,
        engine_name=request.engine,
    )
    
    run = create_analysis_run(
        grid_id=grid.grid_id,
        scenario_id=None,
        case_study_id=None,
        engine=result.engine,
        engine_version=result.engine_version,
        input_hash=input_hash,
        result=result
    )
    result.analysis_id = run.id
    result.input_hash = input_hash
    return result


@router.post("/grids/{grid_id}/what-if", response_model=PowerFlowResult)
def run_what_if(grid_id: str, request: WhatIfRequest) -> PowerFlowResult:
    grid = grid_service.get_grid(grid_id)
    
    scenario_mods = {
        "solar_output_mw": request.solar_output_mw,
        "wind_output_mw": request.wind_output_mw,
        "battery_output_mw": request.battery_output_mw,
        "load_scale": request.load_scale,
    }
    input_hash = compute_input_hash(grid, scenario_modifications=scenario_mods, engine=request.engine)
    
    result = what_if_service.run_what_if(grid, request)
    
    run = create_analysis_run(
        grid_id=grid.grid_id,
        scenario_id="what_if",
        case_study_id=None,
        engine=result.engine,
        engine_version=result.engine_version,
        input_hash=input_hash,
        result=result
    )
    result.analysis_id = run.id
    result.input_hash = input_hash
    return result


@router.get("/engines", response_model=EngineRegistryResponse)
def engine_status() -> EngineRegistryResponse:
    registry = build_registry()
    default = registry.default(settings.default_engine).name
    return EngineRegistryResponse(
        engines=registry.info_all(),
        default_engine=default,
    )


@router.get("/engines/scilab/status", response_model=ScilabStatusResponse)
def scilab_status() -> ScilabStatusResponse:
    return ScilabStatusResponse(**scilab_status_payload(settings))


@router.post("/compare-engines", response_model=EngineComparisonResponse)
def compare_engines_endpoint(
    request: EngineComparisonRequest,
) -> EngineComparisonResponse:
    return compare_engines(
        request.grid,
        tolerance=request.tolerance,
        max_iterations=request.max_iterations,
        voltage_tolerance=request.voltage_tolerance,
        angle_tolerance_deg=request.angle_tolerance_deg,
        flow_tolerance_pu=request.flow_tolerance_pu,
    )
