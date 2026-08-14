from app.domain.enums import BusType
from app.domain.models import GridModel
from app.schemas.grid import ValidationIssue


def _issue(code: str, message: str, location: str = "") -> ValidationIssue:
    return ValidationIssue(code=code, message=message, location=location)


def _check_duplicates(items, field: str, label: str, issues: list[ValidationIssue]):
    seen: dict[str, list[str]] = {}
    for item in items:
        key = getattr(item, field)
        seen.setdefault(key, []).append(item.id)
    for key, ids in seen.items():
        if len(ids) > 1:
            issues.append(
                _issue(
                    "duplicate_id",
                    f"Duplicate {label} identifier '{key}' used by {len(ids)} entries.",
                    label,
                )
            )


def validate_grid(grid: GridModel) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not grid.buses:
        issues.append(_issue("no_buses", "Grid must contain at least one bus.", "buses"))

    if grid.base_mva <= 0:
        issues.append(
            _issue("invalid_base_mva", "Base MVA must be positive.", "base_mva")
        )

    slack_buses = [bus for bus in grid.buses if bus.type == BusType.SLACK]
    if not slack_buses:
        issues.append(_issue("missing_slack", "Grid must have exactly one slack bus.", "buses"))
    elif len(slack_buses) > 1:
        issues.append(
            _issue(
                "multiple_slack",
                f"Grid must have exactly one slack bus, found {len(slack_buses)}.",
                "buses",
            )
        )

    _check_duplicates(grid.buses, "id", "bus", issues)
    _check_duplicates(grid.lines, "id", "line", issues)
    _check_duplicates(grid.generators, "id", "generator", issues)
    _check_duplicates(grid.loads, "id", "load", issues)

    bus_ids = {bus.id for bus in grid.buses}
    adjacency: dict[str, list[str]] = {bus.id: [] for bus in grid.buses}

    for line in grid.lines:
        if line.from_bus not in bus_ids:
            issues.append(
                _issue(
                    "invalid_line_bus_reference",
                    f"Line '{line.id}' references unknown from_bus '{line.from_bus}'.",
                    "lines",
                )
            )
        if line.to_bus not in bus_ids:
            issues.append(
                _issue(
                    "invalid_line_bus_reference",
                    f"Line '{line.id}' references unknown to_bus '{line.to_bus}'.",
                    "lines",
                )
            )
        if line.from_bus == line.to_bus:
            issues.append(
                _issue(
                    "line_self_loop",
                    f"Line '{line.id}' connects a bus to itself.",
                    "lines",
                )
            )
        if line.reactance == 0:
            issues.append(
                _issue(
                    "invalid_line_parameters",
                    f"Line '{line.id}' has zero reactance.",
                    "lines",
                )
            )
        if line.resistance < 0:
            issues.append(
                _issue(
                    "invalid_line_parameters",
                    f"Line '{line.id}' has negative resistance.",
                    "lines",
                )
            )
        if line.thermal_limit <= 0:
            issues.append(
                _issue(
                    "invalid_line_parameters",
                    f"Line '{line.id}' must have a positive thermal limit.",
                    "lines",
                )
            )
        if line.from_bus in bus_ids and line.to_bus in bus_ids:
            adjacency[line.from_bus].append(line.to_bus)
            adjacency[line.to_bus].append(line.from_bus)

    for generator in grid.generators:
        if generator.bus_id not in bus_ids:
            issues.append(
                _issue(
                    "invalid_generator_bus",
                    f"Generator '{generator.id}' references unknown bus '{generator.bus_id}'.",
                    "generators",
                )
            )

    for load in grid.loads:
        if load.bus_id not in bus_ids:
            issues.append(
                _issue(
                    "invalid_load_bus",
                    f"Load '{load.id}' references unknown bus '{load.bus_id}'.",
                    "loads",
                )
            )

    if grid.buses:
        visited: set[str] = set()
        stack = [grid.buses[0].id]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            stack.extend(neighbor for neighbor in adjacency[node] if neighbor not in visited)
        unreachable = [bus.id for bus in grid.buses if bus.id not in visited]
        if unreachable:
            issues.append(
                _issue(
                    "disconnected_network",
                    f"Network is disconnected; buses not reachable: {sorted(unreachable)}.",
                    "lines",
                )
            )

    return issues


def is_valid(grid: GridModel) -> bool:
    return not validate_grid(grid)
