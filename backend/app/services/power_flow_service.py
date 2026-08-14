from __future__ import annotations

import time

from app.core.config import Settings, settings as default_settings
from app.core.exceptions import InvalidEngine, InvalidGrid, PowerFlowDidNotConverge
from app.domain.models import GridModel
from app.power_system.engines import build_registry
from app.power_system.results import PowerFlowResult, build_failed_result
from app.services.validation_service import validate_grid


def run_power_flow(
    grid: GridModel,
    tolerance: float | None = None,
    max_iterations: int | None = None,
    engine_name: str | None = None,
    settings: Settings = default_settings,
) -> PowerFlowResult:
    issues = validate_grid(grid)
    if issues:
        raise InvalidGrid(
            "Grid is invalid and cannot be analyzed.",
            details=[issue.model_dump() for issue in issues],
        )

    registry = build_registry()
    engine = registry.select(engine_name or settings.default_engine)
    if engine is None:
        raise InvalidEngine(
            f"Power-flow engine '{engine_name or settings.default_engine}' is not available."
        )

    started = time.perf_counter()
    try:
        result = engine.run(
            grid,
            tolerance or settings.tolerance,
            max_iterations or settings.max_iterations,
            settings,
        )
    except PowerFlowDidNotConverge as exc:
        failed = build_failed_result(grid, engine.name, exc.iterations, exc.max_mismatch)
        failed.execution_time_ms = (time.perf_counter() - started) * 1000.0
        return failed

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    result.execution_time_ms = elapsed_ms
    return result
