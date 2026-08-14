from dataclasses import dataclass

import numpy as np

from app.domain.enums import BusType
from app.domain.models import GridModel
from app.power_system.per_unit import power_to_per_unit
from app.power_system.ybus import YBus


@dataclass
class PowerFlowSolution:
    converged: bool
    iterations: int
    max_mismatch: float
    voltage_magnitude: np.ndarray
    voltage_angle: np.ndarray


@dataclass
class _Specs:
    types: list[BusType]
    voltage_init: np.ndarray
    angle_init: np.ndarray
    p_spec: np.ndarray
    q_spec: np.ndarray


def _build_specs(grid: GridModel, ybus: YBus) -> _Specs:
    n = len(grid.buses)
    types = [bus.type for bus in grid.buses]
    voltage_init = np.zeros(n)
    angle_init = np.zeros(n)
    p_spec = np.zeros(n)
    q_spec = np.zeros(n)

    for i, bus in enumerate(grid.buses):
        if bus.type == BusType.SLACK:
            voltage_init[i] = bus.voltage_magnitude
            angle_init[i] = np.deg2rad(bus.voltage_angle)
        elif bus.type == BusType.PV:
            voltage_init[i] = bus.voltage_magnitude
        else:
            voltage_init[i] = 1.0

    for gen in grid.generators:
        i = ybus.bus_index[gen.bus_id]
        p_spec[i] += power_to_per_unit(gen.active_power, grid.base_mva)
        q_spec[i] += power_to_per_unit(gen.reactive_power, grid.base_mva)

    for load in grid.loads:
        i = ybus.bus_index[load.bus_id]
        p_spec[i] -= power_to_per_unit(load.active_power, grid.base_mva)
        q_spec[i] -= power_to_per_unit(load.reactive_power, grid.base_mva)

    return _Specs(types, voltage_init, angle_init, p_spec, q_spec)


def _power_injections(
    v: np.ndarray,
    theta: np.ndarray,
    g: np.ndarray,
    b: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    n = len(v)
    p = np.zeros(n)
    q = np.zeros(n)
    for i in range(n):
        for j in range(n):
            angle_diff = theta[i] - theta[j]
            p[i] += v[i] * v[j] * (g[i, j] * np.cos(angle_diff) + b[i, j] * np.sin(angle_diff))
            q[i] += v[i] * v[j] * (g[i, j] * np.sin(angle_diff) - b[i, j] * np.cos(angle_diff))
    return p, q


def _jacobian(
    v: np.ndarray,
    theta: np.ndarray,
    g: np.ndarray,
    b: np.ndarray,
    p: np.ndarray,
    q: np.ndarray,
    non_slack: list[int],
    pq: list[int],
) -> np.ndarray:
    n = len(v)
    h = np.zeros((n, n))
    n_block = np.zeros((n, n))
    j_block = np.zeros((n, n))
    l_block = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            angle_diff = theta[i] - theta[j]
            if i == j:
                h[i, i] = -q[i] - b[i, i] * v[i] ** 2
                n_block[i, i] = p[i] + g[i, i] * v[i] ** 2
                j_block[i, i] = p[i] - g[i, i] * v[i] ** 2
                l_block[i, i] = q[i] - b[i, i] * v[i] ** 2
            else:
                h[i, j] = v[i] * v[j] * (g[i, j] * np.sin(angle_diff) - b[i, j] * np.cos(angle_diff))
                n_block[i, j] = v[i] * v[j] * (g[i, j] * np.cos(angle_diff) + b[i, j] * np.sin(angle_diff))
                j_block[i, j] = -v[i] * v[j] * (g[i, j] * np.cos(angle_diff) + b[i, j] * np.sin(angle_diff))
                l_block[i, j] = v[i] * v[j] * (g[i, j] * np.sin(angle_diff) - b[i, j] * np.cos(angle_diff))

    top = np.hstack([h[np.ix_(non_slack, non_slack)], n_block[np.ix_(non_slack, pq)]])
    bottom = np.hstack([j_block[np.ix_(pq, non_slack)], l_block[np.ix_(pq, pq)]])
    return np.vstack([top, bottom])


def solve_power_flow(
    grid: GridModel,
    ybus: YBus,
    tolerance: float = 1e-6,
    max_iterations: int = 20,
) -> PowerFlowSolution:
    specs = _build_specs(grid, ybus)
    n = len(grid.buses)

    non_slack = [i for i, t in enumerate(specs.types) if t != BusType.SLACK]
    pq = [i for i, t in enumerate(specs.types) if t == BusType.PQ]

    voltage = specs.voltage_init.copy()
    angle = specs.angle_init.copy()
    g = ybus.matrix.real
    b = ybus.matrix.imag

    last_mismatch = 0.0

    for iteration in range(1, max_iterations + 1):
        p, q = _power_injections(voltage, angle, g, b)

        mismatch = np.concatenate(
            [
                specs.p_spec[non_slack] - p[non_slack],
                specs.q_spec[pq] - q[pq],
            ]
        )
        last_mismatch = float(np.max(np.abs(mismatch))) if mismatch.size else 0.0

        if last_mismatch < tolerance:
            return PowerFlowSolution(
                converged=True,
                iterations=iteration,
                max_mismatch=last_mismatch,
                voltage_magnitude=voltage.copy(),
                voltage_angle=angle.copy(),
            )

        jacobian = _jacobian(voltage, angle, g, b, p, q, non_slack, pq)
        try:
            delta = np.linalg.solve(jacobian, mismatch)
        except np.linalg.LinAlgError:
            return PowerFlowSolution(
                converged=False,
                iterations=iteration,
                max_mismatch=last_mismatch,
                voltage_magnitude=voltage.copy(),
                voltage_angle=angle.copy(),
            )

        theta_count = len(non_slack)
        angle[non_slack] += delta[:theta_count]
        voltage[pq] *= 1.0 + delta[theta_count:]

    return PowerFlowSolution(
        converged=False,
        iterations=max_iterations,
        max_mismatch=last_mismatch,
        voltage_magnitude=voltage.copy(),
        voltage_angle=angle.copy(),
    )
