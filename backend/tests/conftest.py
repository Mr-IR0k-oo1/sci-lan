import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.domain.models import GridModel  # noqa: E402

SAMPLE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "sample_grid.json")


@pytest.fixture
def sample_grid() -> GridModel:
    with open(SAMPLE_PATH) as handle:
        return GridModel.model_validate(json.load(handle))


def _base_two_bus_grid() -> GridModel:
    return GridModel(
        grid_id="two-bus",
        name="Two Bus",
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
