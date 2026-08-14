from app.domain.enums import BusType
from app.domain.models import GridModel
from app.services.validation_service import validate_grid


def _without_slack(grid: GridModel) -> GridModel:
    buses = [bus for bus in grid.buses if bus.type != BusType.SLACK]
    buses[0] = buses[0].model_copy(update={"type": BusType.PQ})
    return grid.model_copy(update={"buses": buses})


def _with_second_slack(grid: GridModel) -> GridModel:
    buses = [
        bus.model_copy(update={"type": BusType.SLACK}) if bus.id == "B2" else bus
        for bus in grid.buses
    ]
    return grid.model_copy(update={"buses": buses})


def _no_buses(grid: GridModel) -> GridModel:
    return grid.model_copy(update={"buses": [], "lines": [], "generators": [], "loads": []})


def _codes(issues):
    return [issue.code for issue in issues]


def test_valid_sample_grid_passes(sample_grid):
    assert validate_grid(sample_grid) == []


def test_no_buses(sample_grid):
    issues = validate_grid(_no_buses(sample_grid))
    assert "no_buses" in _codes(issues)


def test_missing_slack(sample_grid):
    issues = validate_grid(_without_slack(sample_grid))
    assert "missing_slack" in _codes(issues)


def test_multiple_slack(sample_grid):
    issues = validate_grid(_with_second_slack(sample_grid))
    assert "multiple_slack" in _codes(issues)


def test_invalid_line_bus_reference(sample_grid):
    lines = [
        line.model_copy(update={"from_bus": "NOPE"}) if line.id == "L1" else line
        for line in sample_grid.lines
    ]
    issues = validate_grid(sample_grid.model_copy(update={"lines": lines}))
    assert "invalid_line_bus_reference" in _codes(issues)


def test_duplicate_ids(sample_grid):
    buses = [
        bus.model_copy(update={"id": "DUP"}) if bus.id in {"B2", "B3"} else bus
        for bus in sample_grid.buses
    ]
    issues = validate_grid(sample_grid.model_copy(update={"buses": buses}))
    assert "duplicate_id" in _codes(issues)


def test_disconnected_network(sample_grid):
    lines = [line for line in sample_grid.lines if line.from_bus != "B4" and line.to_bus != "B4"]
    issues = validate_grid(sample_grid.model_copy(update={"lines": lines}))
    assert "disconnected_network" in _codes(issues)


def test_invalid_base_mva(sample_grid):
    issues = validate_grid(sample_grid.model_copy(update={"base_mva": 0}))
    assert "invalid_base_mva" in _codes(issues)
    issues = validate_grid(sample_grid.model_copy(update={"base_mva": -50}))
    assert "invalid_base_mva" in _codes(issues)


def test_line_zero_reactance(sample_grid):
    lines = [
        line.model_copy(update={"reactance": 0.0}) if line.id == "L1" else line
        for line in sample_grid.lines
    ]
    issues = validate_grid(sample_grid.model_copy(update={"lines": lines}))
    assert "invalid_line_parameters" in _codes(issues)


def test_line_negative_thermal_limit(sample_grid):
    lines = [
        line.model_copy(update={"thermal_limit": -10}) if line.id == "L1" else line
        for line in sample_grid.lines
    ]
    issues = validate_grid(sample_grid.model_copy(update={"lines": lines}))
    assert "invalid_line_parameters" in _codes(issues)


def test_invalid_generator_bus(sample_grid):
    generators = [
        gen.model_copy(update={"bus_id": "NOPE"}) if gen.id == "G2" else gen
        for gen in sample_grid.generators
    ]
    issues = validate_grid(sample_grid.model_copy(update={"generators": generators}))
    assert "invalid_generator_bus" in _codes(issues)


def test_invalid_load_bus(sample_grid):
    loads = [load.model_copy(update={"bus_id": "NOPE"}) for load in sample_grid.loads]
    issues = validate_grid(sample_grid.model_copy(update={"loads": loads}))
    assert "invalid_load_bus" in _codes(issues)
