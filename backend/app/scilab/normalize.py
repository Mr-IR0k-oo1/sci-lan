"""Normalize a raw Scilab result into the shared ``PowerFlowResult`` contract.

The normalized result is byte-for-byte the same contract produced by the Python
engine, so stress analysis, comparisons, recommendations, mitigation testing,
API responses and frontend visualization behave identically regardless of which
engine executed the solve.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.core.exceptions import ScilabUnavailable
from app.domain.enums import BusType, GeneratorType, LineStatus
from app.domain.models import GridModel
from app.power_system.impact_score import compute_impact_score
from app.power_system.per_unit import power_from_per_unit
from app.power_system.results import (
    BusResult,
    LineResult,
    PowerFlowResult,
    PowerFlowSummary,
    _bus_status,
    _line_status,
)


def normalize_scilab_result(
    raw: dict[str, Any],
    grid: GridModel,
    engine_version: str | None,
    settings: Settings,
    execution_time_ms: float = 0.0,
) -> PowerFlowResult:
    """Build a ``PowerFlowResult`` from the raw Scilab result dict."""
    try:
        converged = bool(raw["converged"])
        iterations = int(raw["iterations"])
        max_mismatch = float(raw["max_mismatch"])
        buses_raw = raw["buses"]
        lines_raw = raw.get("lines", [])
    except (KeyError, TypeError, ValueError) as exc:
        raise ScilabUnavailable(
            f"Scilab result is missing required fields: {exc}"
        ) from exc

    if not converged:
        return PowerFlowResult(
            grid_id=grid.grid_id,
            engine="scilab",
            engine_version=engine_version,
            status="not_converged",
            converged=False,
            iterations=iterations,
            max_mismatch=max_mismatch,
            buses=[],
            lines=[],
            summary=None,
        )

    if len(buses_raw) != len(grid.buses):
        raise ScilabUnavailable(
            "Scilab returned a bus count that does not match the grid."
        )

    base_mva = grid.base_mva

    bus_results: list[BusResult] = []
    voltage = [0.0] * len(grid.buses)
    for i, bus in enumerate(grid.buses):
        entry = buses_raw[i]
        v = float(entry["V"])
        theta_deg = float(entry["theta_deg"])
        p_pu = float(entry.get("P_pu", 0.0))
        q_pu = float(entry.get("Q_pu", 0.0))
        voltage[i] = v
        bus_results.append(
            BusResult(
                bus_id=bus.id,
                voltage_magnitude=v,
                voltage_angle=theta_deg,
                active_power=power_from_per_unit(p_pu, base_mva),
                reactive_power=power_from_per_unit(q_pu, base_mva),
                status=_bus_status(v, settings),
            )
        )

    line_results: list[LineResult] = []
    flows_by_index: dict[int, dict[str, Any]] = {
        int(entry.get("index", i)): entry for i, entry in enumerate(lines_raw)
    }
    for i, line in enumerate(grid.lines):
        flow = flows_by_index.get(i, {})
        p_from_pu = float(flow.get("P_from_pu", 0.0))
        q_from_pu = float(flow.get("Q_from_pu", 0.0))
        p_to_pu = float(flow.get("P_to_pu", 0.0))
        q_to_pu = float(flow.get("Q_to_pu", 0.0))

        loading = (
            (p_from_pu**2 + q_from_pu**2) ** 0.5 * base_mva / line.thermal_limit * 100.0
            if line.thermal_limit > 0
            else 0.0
        )
        line_results.append(
            LineResult(
                line_id=line.id,
                from_bus=line.from_bus,
                to_bus=line.to_bus,
                active_power_from=power_from_per_unit(p_from_pu, base_mva),
                reactive_power_from=power_from_per_unit(q_from_pu, base_mva),
                active_power_to=power_from_per_unit(p_to_pu, base_mva),
                reactive_power_to=power_from_per_unit(q_to_pu, base_mva),
                loading_percentage=float(loading),
                status=_line_status(float(loading), settings),
            )
        )

    summary = _build_summary(grid, bus_results, line_results, voltage)
    impact_score = compute_impact_score(
        minimum_voltage_pu=summary.minimum_voltage_pu,
        maximum_voltage_pu=summary.maximum_voltage_pu,
        maximum_line_loading=summary.maximum_line_loading,
        overloaded_lines=summary.overloaded_lines,
        total_losses_mw=summary.total_losses_mw,
        total_load_mw=summary.total_load_mw,
        settings=settings,
    )

    return PowerFlowResult(
        grid_id=grid.grid_id,
        engine="scilab",
        engine_version=engine_version,
        status="success",
        converged=True,
        iterations=iterations,
        max_mismatch=max_mismatch,
        execution_time_ms=execution_time_ms,
        buses=bus_results,
        lines=line_results,
        summary=summary,
        impact_score=impact_score,
    )


def _build_summary(
    grid: GridModel,
    bus_results: list[BusResult],
    line_results: list[LineResult],
    voltage: list[float],
) -> PowerFlowSummary:
    slack_index = next(
        (i for i, bus in enumerate(grid.buses) if bus.type == BusType.SLACK),
        None,
    )
    slack_generation = (
        max(bus_results[slack_index].active_power, 0.0)
        if slack_index is not None
        else 0.0
    )
    other_generation = sum(
        gen.active_power for gen in grid.generators if gen.bus_id != (grid.buses[slack_index].id if slack_index is not None else None)
    )
    total_generation = slack_generation + other_generation
    renewable_generation = sum(
        gen.active_power
        for gen in grid.generators
        if gen.type in (GeneratorType.SOLAR, GeneratorType.WIND)
    )
    total_load = sum(load.active_power for load in grid.loads)
    maximum_loading = max(
        (line.loading_percentage for line in line_results), default=0.0
    )

    return PowerFlowSummary(
        total_generation_mw=total_generation,
        renewable_generation_mw=renewable_generation,
        total_load_mw=total_load,
        total_losses_mw=total_generation - total_load,
        minimum_voltage_pu=min(voltage) if voltage else 0.0,
        maximum_voltage_pu=max(voltage) if voltage else 0.0,
        maximum_line_loading=float(maximum_loading),
        overloaded_lines=sum(1 for r in line_results if r.status == LineStatus.OVERLOADED),
    )
