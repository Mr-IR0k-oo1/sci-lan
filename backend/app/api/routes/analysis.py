from fastapi import APIRouter

from app.core.config import settings
from app.power_system.engines import build_registry
from app.power_system.results import PowerFlowResult
from app.schemas.analysis import EngineRegistryResponse, PowerFlowRequest, WhatIfRequest
from app.services import grid_service, power_flow_service, what_if_service

router = APIRouter(tags=["analysis"])


@router.post("/grids/{grid_id}/analyze/power-flow", response_model=PowerFlowResult)
def run_power_flow(grid_id: str, request: PowerFlowRequest) -> PowerFlowResult:
    grid = grid_service.get_grid(grid_id)
    return power_flow_service.run_power_flow(
        grid,
        tolerance=request.tolerance,
        max_iterations=request.max_iterations,
        engine_name=request.engine,
    )


@router.post("/grids/{grid_id}/what-if", response_model=PowerFlowResult)
def run_what_if(grid_id: str, request: WhatIfRequest) -> PowerFlowResult:
    grid = grid_service.get_grid(grid_id)
    return what_if_service.run_what_if(grid, request)


@router.get("/engines", response_model=EngineRegistryResponse)
def engine_status() -> EngineRegistryResponse:
    registry = build_registry()
    default = registry.default(settings.default_engine).name
    return EngineRegistryResponse(
        engines=registry.info_all(),
        default_engine=default,
    )
