import uuid

from app.core.exceptions import GridNotFound
from app.schemas.scenario import Scenario, ScenarioCreateRequest

_storage: dict[str, dict[str, Scenario]] = {}


def create_scenario(grid_id: str, request: ScenarioCreateRequest) -> Scenario:
    if grid_id not in _storage:
        _storage[grid_id] = {}
    scenario_id = request.id or uuid.uuid4().hex[:8]
    scenario = Scenario(
        id=scenario_id,
        name=request.name,
        grid=request.grid,
    )
    _storage[grid_id][scenario_id] = scenario
    return scenario


def get_scenario(grid_id: str, scenario_id: str) -> Scenario:
    scenarios = _storage.get(grid_id, {})
    if scenario_id not in scenarios:
        raise GridNotFound(f"scenario/{scenario_id}")
    return scenarios[scenario_id]


def list_scenarios(grid_id: str) -> list[Scenario]:
    return list(_storage.get(grid_id, {}).values())


def delete_scenario(grid_id: str, scenario_id: str) -> None:
    scenarios = _storage.get(grid_id, {})
    if scenario_id not in scenarios:
        raise GridNotFound(f"scenario/{scenario_id}")
    del scenarios[scenario_id]


def clear_scenarios() -> None:
    _storage.clear()
