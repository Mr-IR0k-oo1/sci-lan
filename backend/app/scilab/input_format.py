"""Normalized power-flow input format.

The Scilab engine does not consume the internal `GridModel` directly; instead a
flat, engine-agnostic structure is derived from it. This structure is what gets
serialized into the temporary execution directory. No second independent grid
model exists — ``build_normalized_input`` is the single projection from the
domain model.

Documented format::

    {
        "base_mva": 100.0,
        "tolerance": 1e-6,
        "max_iterations": 20,
        "buses": [
            {"index": 0, "id": "B1", "type": "SLACK",
             "voltage_magnitude": 1.0, "voltage_angle": 0.0}
        ],
        "lines": [
            {"from_index": 0, "to_index": 1, "resistance": 0.01,
             "reactance": 0.05, "susceptance": 0.0, "thermal_limit": 100}
        ],
        "generators": [],
        "loads": []
    }

All powers are in per-unit on ``base_mva``; angles are in degrees.
"""

from __future__ import annotations

from app.domain.enums import BusType
from app.domain.models import GridModel
from app.power_system.per_unit import power_to_per_unit

# Type codes used by the Scilab Newton-Raphson implementation.
TYPE_CODE: dict[BusType, int] = {
    BusType.SLACK: 1,
    BusType.PV: 2,
    BusType.PQ: 3,
}


def build_normalized_input(
    grid: GridModel,
    tolerance: float,
    max_iterations: int,
) -> dict:
    """Project a ``GridModel`` into the documented normalized input structure."""
    index = {bus.id: i for i, bus in enumerate(grid.buses)}

    buses = [
        {
            "index": i,
            "id": bus.id,
            "type": bus.type.value,
            "voltage_magnitude": bus.voltage_magnitude,
            "voltage_angle": bus.voltage_angle,
        }
        for i, bus in enumerate(grid.buses)
    ]

    lines = [
        {
            "from_index": index[line.from_bus],
            "to_index": index[line.to_bus],
            "resistance": line.resistance,
            "reactance": line.reactance,
            "susceptance": line.susceptance,
            "thermal_limit": line.thermal_limit,
        }
        for line in grid.lines
    ]

    generators = [
        {
            "id": gen.id,
            "bus_index": index[gen.bus_id],
            "type": gen.type.value,
            "active_power_pu": power_to_per_unit(gen.active_power, grid.base_mva),
            "reactive_power_pu": power_to_per_unit(gen.reactive_power, grid.base_mva),
            "active_power_max_mw": gen.active_power_max,
            "reactive_power_min_mvAr": gen.reactive_power_min,
            "reactive_power_max_mvAr": gen.reactive_power_max,
        }
        for gen in grid.generators
    ]

    loads = [
        {
            "id": load.id,
            "bus_index": index[load.bus_id],
            "active_power_pu": power_to_per_unit(load.active_power, grid.base_mva),
            "reactive_power_pu": power_to_per_unit(load.reactive_power, grid.base_mva),
        }
        for load in grid.loads
    ]

    return {
        "base_mva": grid.base_mva,
        "tolerance": tolerance,
        "max_iterations": max_iterations,
        "buses": buses,
        "lines": lines,
        "generators": generators,
        "loads": loads,
    }


def render_scilab_input_variables(
    grid: GridModel,
    tolerance: float,
    max_iterations: int,
) -> str:
    """Serialize the normalized input as safe Scilab variable definitions.

    Values are numbers rendered with the shortest round-trip representation;
    nothing user-supplied is ever treated as code.
    """
    index = {bus.id: i for i, bus in enumerate(grid.buses)}
    parts: list[str] = []

    def fmt(value: float) -> str:
        return f"{value:.9g}"

    parts.append(f"base_mva = {fmt(grid.base_mva)};")
    parts.append(f"tolerance = {fmt(tolerance)};")
    parts.append(f"max_iterations = {int(max_iterations)};")
    parts.append(f"bus_count = {len(grid.buses)};")
    parts.append("bus_type = [" + ", ".join(str(TYPE_CODE[bus.type]) for bus in grid.buses) + "];")

    bus_v0: list[str] = []
    bus_theta0: list[str] = []
    for bus in grid.buses:
        if bus.type == BusType.SLACK:
            bus_v0.append(fmt(bus.voltage_magnitude))
            bus_theta0.append(fmt(bus.voltage_angle))
        elif bus.type == BusType.PV:
            bus_v0.append(fmt(bus.voltage_magnitude))
            bus_theta0.append("0")
        else:
            bus_v0.append("1")
            bus_theta0.append("0")
    parts.append("bus_v0 = [" + ", ".join(bus_v0) + "];")
    parts.append("bus_theta0_deg = [" + ", ".join(bus_theta0) + "];")

    p_spec = [0.0] * len(grid.buses)
    q_spec = [0.0] * len(grid.buses)
    for gen in grid.generators:
        i = index[gen.bus_id]
        p_spec[i] += power_to_per_unit(gen.active_power, grid.base_mva)
        q_spec[i] += power_to_per_unit(gen.reactive_power, grid.base_mva)
    for load in grid.loads:
        i = index[load.bus_id]
        p_spec[i] -= power_to_per_unit(load.active_power, grid.base_mva)
        q_spec[i] -= power_to_per_unit(load.reactive_power, grid.base_mva)
    parts.append("bus_p_spec = [" + ", ".join(fmt(v) for v in p_spec) + "];")
    parts.append("bus_q_spec = [" + ", ".join(fmt(v) for v in q_spec) + "];")

    line_rows = []
    for line in grid.lines:
        i = index[line.from_bus] + 1
        j = index[line.to_bus] + 1
        line_rows.append(
            f"{i} {j} {fmt(line.resistance)} {fmt(line.reactance)} {fmt(line.susceptance)}"
        )
    parts.append(f"line_count = {len(grid.lines)};")
    if line_rows:
        parts.append("lines = [")
        parts.append(";".join("[" + row + "]" for row in line_rows))
        parts.append("];")
    else:
        parts.append("lines = [];")

    return "\n".join(parts) + "\n"
