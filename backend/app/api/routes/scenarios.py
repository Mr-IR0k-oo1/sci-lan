from fastapi import APIRouter, status

from app.power_system.results import PowerFlowResult
from app.schemas.analysis import PowerFlowRequest
from app.schemas.scenario import Scenario, ScenarioCreateRequest, ScenarioSummary
from app.services import grid_service, power_flow_service, scenario_service

router = APIRouter(tags=["scenarios"])


@router.get("/grids/{grid_id}/scenarios", response_model=list[ScenarioSummary])
def list_scenarios(grid_id: str) -> list[ScenarioSummary]:
    grid_service.get_grid(grid_id)
    return [
        ScenarioSummary(id=scenario.id, name=scenario.name)
        for scenario in scenario_service.list_scenarios(grid_id)
    ]


@router.post("/grids/{grid_id}/scenarios", response_model=Scenario, status_code=status.HTTP_201_CREATED)
def create_scenario(grid_id: str, request: ScenarioCreateRequest) -> Scenario:
    grid_service.get_grid(grid_id)
    return scenario_service.create_scenario(grid_id, request)


@router.post(
    "/grids/{grid_id}/scenarios/{scenario_id}/analyze",
    response_model=PowerFlowResult,
)
def analyze_scenario(
    grid_id: str,
    scenario_id: str,
    request: PowerFlowRequest,
) -> PowerFlowResult:
    grid_service.get_grid(grid_id)
    scenario = scenario_service.get_scenario(grid_id, scenario_id)
    return power_flow_service.run_power_flow(
        scenario.grid,
        tolerance=request.tolerance,
        max_iterations=request.max_iterations,
        engine_name=request.engine,
    )


@router.delete("/grids/{grid_id}/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(grid_id: str, scenario_id: str) -> None:
    grid_service.get_grid(grid_id)
    scenario_service.delete_scenario(grid_id, scenario_id)
