import numpy as np
import pytest

from app.core.config import settings
from app.core.exceptions import InvalidGrid
from app.domain.enums import BusType
from app.domain.models import GridModel
from app.power_system.power_flow import solve_power_flow
from app.power_system.ybus import build_ybus
from app.services import power_flow_service


def _solve(grid: GridModel, tolerance=1e-8, max_iterations=50):
    return solve_power_flow(grid, build_ybus(grid), tolerance, max_iterations)


def _two_bus_grid() -> GridModel:
    return GridModel(
        grid_id="two-bus",
        base_mva=100.0,
        buses=[
            {"id": "B1", "name": "Slack", "type": "SLACK", "voltage_magnitude": 1.0, "voltage_angle": 0.0},
            {"id": "B2", "name": "Load Bus", "type": "PQ"},
        ],
        lines=[
            {"id": "L1", "from_bus": "B1", "to_bus": "B2", "resistance": 0.01, "reactance": 0.05, "susceptance": 0.0, "thermal_limit": 100},
        ],
        generators=[
            {"id": "G1", "bus_id": "B1", "active_power": 0.0, "reactive_power": 0.0},
        ],
        loads=[
            {"id": "D1", "bus_id": "B2", "active_power": 50.0, "reactive_power": 20.0},
        ],
    )


def _three_bus_grid() -> GridModel:
    return GridModel(
        grid_id="three-bus",
        base_mva=100.0,
        buses=[
            {"id": "B1", "name": "Slack", "type": "SLACK", "voltage_magnitude": 1.0, "voltage_angle": 0.0},
            {"id": "B2", "name": "PV", "type": "PV", "voltage_magnitude": 1.03},
            {"id": "B3", "name": "PQ", "type": "PQ"},
        ],
        lines=[
            {"id": "L1", "from_bus": "B1", "to_bus": "B2", "resistance": 0.01, "reactance": 0.05, "susceptance": 0.0, "thermal_limit": 150},
            {"id": "L2", "from_bus": "B2", "to_bus": "B3", "resistance": 0.02, "reactance": 0.08, "susceptance": 0.0, "thermal_limit": 120},
        ],
        generators=[
            {"id": "G1", "bus_id": "B1", "active_power": 0.0, "reactive_power": 0.0},
            {"id": "G2", "bus_id": "B2", "active_power": 100.0, "reactive_power": 0.0},
        ],
        loads=[
            {"id": "D1", "bus_id": "B3", "active_power": 80.0, "reactive_power": 30.0},
        ],
    )


def test_two_bus_converges_with_expected_values():
    grid = _two_bus_grid()
    solution = _solve(grid)
    assert solution.converged
    assert solution.iterations <= 20
    assert solution.max_mismatch < 1e-8
    assert np.isclose(solution.voltage_magnitude[1], 0.98449076, atol=1e-5)
    assert np.isclose(np.rad2deg(solution.voltage_angle[1]), -1.3387, atol=1e-3)


def test_three_bus_with_pv_converges():
    grid = _three_bus_grid()
    solution = _solve(grid)
    assert solution.converged
    assert solution.iterations <= 20
    assert np.isclose(solution.voltage_magnitude[1], 1.03, atol=1e-9)
    assert np.isclose(solution.voltage_magnitude[2], 0.98783246, atol=1e-5)
    assert np.isclose(np.rad2deg(solution.voltage_angle[2]), -3.0765, atol=1e-3)


def test_sample_grid_converges(sample_grid):
    solution = _solve(sample_grid, tolerance=settings.tolerance, max_iterations=settings.max_iterations)
    assert solution.converged
    assert solution.iterations <= settings.max_iterations
    assert solution.max_mismatch < settings.tolerance
    voltages = solution.voltage_magnitude
    assert float(np.max(voltages) - np.min(voltages)) > 0.01


def test_maximum_iterations_failure_is_structured():
    grid = _two_bus_grid()
    solution = _solve(grid, tolerance=1e-8, max_iterations=1)
    assert not solution.converged
    assert solution.iterations == 1


def test_service_returns_structured_failure_on_no_convergence():
    grid = _two_bus_grid()
    result = power_flow_service.run_power_flow(grid, max_iterations=1)
    assert result.converged is False
    assert result.status == "not_converged"
    assert result.buses == []
    assert result.lines == []
    assert result.summary is None


def test_service_rejects_invalid_network():
    grid = _two_bus_grid()
    buses = [bus for bus in grid.buses if bus.type != BusType.SLACK]
    buses[0] = buses[0].model_copy(update={"type": BusType.PQ})
    invalid = grid.model_copy(update={"buses": buses})
    with pytest.raises(InvalidGrid):
        power_flow_service.run_power_flow(invalid)


def test_sample_grid_results_balance(sample_grid):
    result = power_flow_service.run_power_flow(sample_grid)
    assert result.status == "success"
    assert result.converged is True
    assert result.summary is not None
    assert result.summary.total_load_mw == 115.0
    assert result.summary.total_losses_mw == pytest.approx(
        result.summary.total_generation_mw - result.summary.total_load_mw
    )
    assert result.summary.total_losses_mw > 0
    assert result.summary.minimum_voltage_pu == pytest.approx(0.99644833, abs=1e-5)
    assert result.summary.maximum_voltage_pu == pytest.approx(1.06, abs=1e-5)
    assert len(result.buses) == 5
    assert len(result.lines) == 7
    assert all(line.status.value in {"NORMAL", "WARNING", "OVERLOADED"} for line in result.lines)
