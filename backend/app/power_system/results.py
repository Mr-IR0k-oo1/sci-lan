import numpy as np
from pydantic import BaseModel

from app.core.config import Settings
from app.domain.enums import BusStatus, BusType, LineStatus
from app.domain.models import GridModel
from app.power_system.per_unit import power_from_per_unit
from app.power_system.power_flow import PowerFlowSolution, _power_injections
from app.power_system.ybus import YBus


class BusResult(BaseModel):
    bus_id: str
    voltage_magnitude: float
    voltage_angle: float
    active_power: float
    reactive_power: float
    status: BusStatus


class LineResult(BaseModel):
    line_id: str
    from_bus: str
    to_bus: str
    active_power_from: float
    reactive_power_from: float
    active_power_to: float
    reactive_power_to: float
    loading_percentage: float
    status: LineStatus


class PowerFlowSummary(BaseModel):
    total_generation_mw: float
    total_load_mw: float
    total_losses_mw: float
    minimum_voltage_pu: float
    maximum_voltage_pu: float
    overloaded_lines: int


class PowerFlowResult(BaseModel):
    grid_id: str
    engine: str
    status: str
    converged: bool
    iterations: int
    max_mismatch: float
    buses: list[BusResult]
    lines: list[LineResult]
    summary: PowerFlowSummary | None


def _bus_status(voltage_pu: float, settings: Settings) -> BusStatus:
    if voltage_pu < settings.voltage_critical_low or voltage_pu > settings.voltage_critical_high:
        return BusStatus.CRITICAL
    if voltage_pu < settings.voltage_warning_low or voltage_pu > settings.voltage_warning_high:
        return BusStatus.WARNING
    return BusStatus.NORMAL


def _line_status(loading_percent: float, settings: Settings) -> LineStatus:
    if loading_percent > settings.line_overload_threshold:
        return LineStatus.OVERLOADED
    if loading_percent >= settings.line_warning_threshold:
        return LineStatus.WARNING
    return LineStatus.NORMAL


def _line_flows(grid: GridModel, ybus: YBus, voltage: np.ndarray, angle: np.ndarray):
    for line in grid.lines:
        i = ybus.bus_index[line.from_bus]
        j = ybus.bus_index[line.to_bus]
        series = 1.0 / complex(line.resistance, line.reactance)
        shunt = complex(0.0, line.susceptance / 2.0)

        v_from = voltage[i] * np.exp(1j * angle[i])
        v_to = voltage[j] * np.exp(1j * angle[j])
        i_from = (v_from - v_to) * series + v_from * shunt
        i_to = (v_to - v_from) * series + v_to * shunt

        apparent_from = v_from * np.conj(i_from)
        apparent_to = v_to * np.conj(i_to)
        yield line, apparent_from, apparent_to


def build_power_flow_result(
    grid: GridModel,
    ybus: YBus,
    solution: PowerFlowSolution,
    engine_name: str,
    settings: Settings,
) -> PowerFlowResult:
    if not solution.converged:
        return PowerFlowResult(
            grid_id=grid.grid_id,
            engine=engine_name,
            status="not_converged",
            converged=False,
            iterations=solution.iterations,
            max_mismatch=solution.max_mismatch,
            buses=[],
            lines=[],
            summary=None,
        )

    voltage = solution.voltage_magnitude
    angle = solution.voltage_angle
    base_mva = grid.base_mva
    p, q = _power_injections(voltage, angle, ybus.matrix.real, ybus.matrix.imag)

    bus_results = []
    for i, bus in enumerate(grid.buses):
        bus_results.append(
            BusResult(
                bus_id=bus.id,
                voltage_magnitude=float(voltage[i]),
                voltage_angle=float(np.rad2deg(angle[i])),
                active_power=power_from_per_unit(float(p[i]), base_mva),
                reactive_power=power_from_per_unit(float(q[i]), base_mva),
                status=_bus_status(float(voltage[i]), settings),
            )
        )

    line_results = []
    for line, apparent_from, apparent_to in _line_flows(grid, ybus, voltage, angle):
        loading = (
            abs(apparent_from) * base_mva / line.thermal_limit * 100.0
            if line.thermal_limit > 0
            else 0.0
        )
        line_results.append(
            LineResult(
                line_id=line.id,
                from_bus=line.from_bus,
                to_bus=line.to_bus,
                active_power_from=power_from_per_unit(float(apparent_from.real), base_mva),
                reactive_power_from=power_from_per_unit(float(apparent_from.imag), base_mva),
                active_power_to=power_from_per_unit(float(apparent_to.real), base_mva),
                reactive_power_to=power_from_per_unit(float(apparent_to.imag), base_mva),
                loading_percentage=float(loading),
                status=_line_status(float(loading), settings),
            )
        )

    slack_index = next(i for i, bus in enumerate(grid.buses) if bus.type == BusType.SLACK)
    slack_generation = power_from_per_unit(max(float(p[slack_index]), 0.0), base_mva)
    other_generation = sum(
        gen.active_power for gen in grid.generators if gen.bus_id != grid.buses[slack_index].id
    )
    total_generation = slack_generation + other_generation
    total_load = sum(load.active_power for load in grid.loads)

    summary = PowerFlowSummary(
        total_generation_mw=total_generation,
        total_load_mw=total_load,
        total_losses_mw=total_generation - total_load,
        minimum_voltage_pu=float(np.min(voltage)),
        maximum_voltage_pu=float(np.max(voltage)),
        overloaded_lines=sum(1 for r in line_results if r.status == LineStatus.OVERLOADED),
    )

    return PowerFlowResult(
        grid_id=grid.grid_id,
        engine=engine_name,
        status="success",
        converged=True,
        iterations=solution.iterations,
        max_mismatch=solution.max_mismatch,
        buses=bus_results,
        lines=line_results,
        summary=summary,
    )


def build_failed_result(
    grid: GridModel,
    engine_name: str,
    iterations: int | None,
    max_mismatch: float | None,
) -> PowerFlowResult:
    return PowerFlowResult(
        grid_id=grid.grid_id,
        engine=engine_name,
        status="not_converged",
        converged=False,
        iterations=iterations or 0,
        max_mismatch=max_mismatch or 0.0,
        buses=[],
        lines=[],
        summary=None,
    )
