"""Engine comparison: run the same grid through the Python and Scilab engines
and quantify the difference between the normalized results.

If Scilab is unavailable the comparison is reported as such — no fake results
are ever produced.
"""

from __future__ import annotations

import time
from typing import Any

from app.core.config import Settings, settings as default_settings
from app.core.exceptions import InvalidGrid, PowerFlowDidNotConverge
from app.domain.models import GridModel
from app.power_system.engines import PythonPowerFlowEngine, ScilabPowerFlowEngine
from app.power_system.results import PowerFlowResult
from app.schemas.analysis import EngineComparisonResponse, EngineRunInfo
from app.scilab.capability import get_capability
from app.services.validation_service import validate_grid

_PYTHON = PythonPowerFlowEngine()
_SCILAB = ScilabPowerFlowEngine()


def _run_safe(engine, grid: GridModel, tolerance: float, max_iterations: int, settings: Settings):
    started = time.perf_counter()
    try:
        result = engine.run(grid, tolerance, max_iterations, settings)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return EngineRunInfo(
            available=True,
            converged=result.converged,
            engine_version=result.engine_version,
            execution_time_ms=round(elapsed_ms, 2),
        ), result
    except PowerFlowDidNotConverge as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return EngineRunInfo(
            available=True,
            converged=False,
            engine_version=engine.engine_version(settings),
            execution_time_ms=round(elapsed_ms, 2),
            error=f"Did not converge after {exc.iterations} iterations.",
        ), None
    except Exception as exc:  # noqa: BLE001 - report engine failures explicitly
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return EngineRunInfo(
            available=True,
            converged=False,
            engine_version=engine.engine_version(settings),
            execution_time_ms=round(elapsed_ms, 2),
            error=str(exc),
        ), None


def _compare_results(
    python: PowerFlowResult,
    scilab: PowerFlowResult,
    grid: GridModel,
    voltage_tolerance: float = 1e-4,
    angle_tolerance_deg: float = 1e-3,
    flow_tolerance_pu: float = 0.02,
) -> dict[str, Any]:
    """Compute maximum differences between two normalized results.

    Voltage and angle differences are compared per bus; line flows are compared
    in per-unit (S_from / S_to) so the numbers are meaningful on any base.
    """
    py_buses = {bus.bus_id: bus for bus in python.buses}
    sc_buses = {bus.bus_id: bus for bus in scilab.buses}

    voltage_diff_max = 0.0
    angle_diff_max = 0.0
    for bus_id, py_bus in py_buses.items():
        sc_bus = sc_buses.get(bus_id)
        if sc_bus is None:
            continue
        voltage_diff_max = max(voltage_diff_max, abs(py_bus.voltage_magnitude - sc_bus.voltage_magnitude))
        angle_diff_max = max(angle_diff_max, abs(py_bus.voltage_angle - sc_bus.voltage_angle))

    py_lines = {line.line_id: line for line in python.lines}
    sc_lines = {line.line_id: line for line in scilab.lines}

    flow_diff_max_pu = 0.0
    for line_id, py_line in py_lines.items():
        sc_line = sc_lines.get(line_id)
        if sc_line is None:
            continue
        for attr in ("active_power_from", "reactive_power_from", "active_power_to", "reactive_power_to"):
            py_pu = getattr(py_line, attr) / grid.base_mva
            sc_pu = getattr(sc_line, attr) / grid.base_mva
            flow_diff_max_pu = max(flow_diff_max_pu, abs(py_pu - sc_pu))

    within_tolerance = (
        voltage_diff_max <= voltage_tolerance
        and angle_diff_max <= angle_tolerance_deg
        and flow_diff_max_pu <= flow_tolerance_pu
    )
    return {
        "voltage_difference_max": round(voltage_diff_max, 6),
        "angle_difference_max": round(angle_diff_max, 6),
        "line_flow_difference_max": round(flow_diff_max_pu, 6),
        "within_tolerance": within_tolerance,
    }


def compare_engines(
    grid: GridModel,
    tolerance: float | None = None,
    max_iterations: int | None = None,
    voltage_tolerance: float = 1e-4,
    angle_tolerance_deg: float = 1e-3,
    flow_tolerance_pu: float = 0.02,
    settings: Settings = default_settings,
) -> EngineComparisonResponse:
    issues = validate_grid(grid)
    if issues:
        raise InvalidGrid(
            "Grid is invalid and cannot be analyzed.",
            details=[issue.model_dump() for issue in issues],
        )

    tolerance = tolerance or settings.tolerance
    max_iterations = max_iterations or settings.max_iterations

    python_info, python_result = _run_safe(_PYTHON, grid, tolerance, max_iterations, settings)

    capability = get_capability(settings)
    if not capability.available:
        return EngineComparisonResponse(
            python=python_info,
            scilab=EngineRunInfo(available=False),
        )

    scilab_info, scilab_result = _run_safe(_SCILAB, grid, tolerance, max_iterations, settings)

    comparison = None
    if python_result is not None and scilab_result is not None:
        comparison = _compare_results(
            python_result,
            scilab_result,
            grid,
            voltage_tolerance,
            angle_tolerance_deg,
            flow_tolerance_pu,
        )

    return EngineComparisonResponse(
        python=python_info,
        scilab=scilab_info,
        comparison=comparison,
    )
