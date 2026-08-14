import numpy as np

from app.domain.models import GridModel
from app.power_system.ybus import build_ybus


def test_ybus_dimensions(sample_grid):
    ybus = build_ybus(sample_grid)
    assert ybus.matrix.shape == (5, 5)
    assert set(ybus.bus_index) == {"B1", "B2", "B3", "B4", "B5"}


def test_ybus_symmetric(sample_grid):
    ybus = build_ybus(sample_grid)
    assert np.allclose(ybus.matrix, ybus.matrix.T)


def test_ybus_two_bus_exact():
    grid = GridModel(
        grid_id="two-bus",
        base_mva=100.0,
        buses=[
            {"id": "B1", "type": "SLACK", "voltage_magnitude": 1.0},
            {"id": "B2", "type": "PQ"},
        ],
        lines=[
            {"id": "L1", "from_bus": "B1", "to_bus": "B2", "resistance": 0.01, "reactance": 0.05, "susceptance": 0.0, "thermal_limit": 100},
        ],
    )
    ybus = build_ybus(grid)
    series = 1.0 / complex(0.01, 0.05)
    expected = np.array([[series, -series], [-series, series]])
    assert np.allclose(ybus.matrix, expected)


def test_ybus_diagonal_includes_charging():
    grid = GridModel(
        grid_id="two-bus",
        base_mva=100.0,
        buses=[
            {"id": "B1", "type": "SLACK", "voltage_magnitude": 1.0},
            {"id": "B2", "type": "PQ"},
        ],
        lines=[
            {"id": "L1", "from_bus": "B1", "to_bus": "B2", "resistance": 0.01, "reactance": 0.05, "susceptance": 0.02, "thermal_limit": 100},
        ],
    )
    ybus = build_ybus(grid)
    series = 1.0 / complex(0.01, 0.05)
    shunt = complex(0.0, 0.01)
    assert np.isclose(ybus.matrix[0, 0], series + shunt)
    assert np.isclose(ybus.matrix[1, 1], series + shunt)
    assert np.isclose(ybus.matrix[0, 1], -series)


def test_ybus_off_diagonal_negative_series(sample_grid):
    ybus = build_ybus(sample_grid)
    series = 1.0 / complex(0.02, 0.08)
    assert np.isclose(ybus.matrix[0, 1], -series)
