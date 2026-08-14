from app.core.config import Settings, settings as default_settings
from app.domain.enums import GeneratorType
from app.domain.models import GridModel
from app.power_system.results import PowerFlowResult
from app.schemas.analysis import WhatIfRequest
from app.services import power_flow_service


def _apply_overrides(base: GridModel, request: WhatIfRequest) -> GridModel:
    grid = (request.grid or base).model_copy()

    generators = []
    for generator in grid.generators:
        updated = generator
        if request.solar_output_mw is not None and generator.type == GeneratorType.SOLAR:
            updated = generator.model_copy(update={"active_power": request.solar_output_mw})
        if request.wind_output_mw is not None and generator.type == GeneratorType.WIND:
            updated = generator.model_copy(update={"active_power": request.wind_output_mw})
        if request.battery_output_mw is not None and generator.type == GeneratorType.STORAGE:
            updated = generator.model_copy(update={"active_power": request.battery_output_mw})
        generators.append(updated)

    loads = []
    for load in grid.loads:
        updated = load
        if request.load_scale is not None:
            updated = load.model_copy(
                update={
                    "active_power": load.active_power * request.load_scale,
                    "reactive_power": load.reactive_power * request.load_scale,
                }
            )
        loads.append(updated)

    return grid.model_copy(update={"generators": generators, "loads": loads})


def run_what_if(
    base: GridModel,
    request: WhatIfRequest,
    settings: Settings = default_settings,
) -> PowerFlowResult:
    modified = _apply_overrides(base, request)
    return power_flow_service.run_power_flow(
        modified,
        tolerance=request.tolerance,
        max_iterations=request.max_iterations,
        engine_name=request.engine,
        settings=settings,
    )
