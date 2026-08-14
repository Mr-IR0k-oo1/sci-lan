"""Transmission stress detection for every line of an analyzed grid."""

from app.config.thresholds import StressThresholds
from app.domain.enums import SeverityLevel
from app.domain.models import GridModel
from app.domain.stress_models import LineStress
from app.power_system.constraints import classify_line
from app.power_system.results import PowerFlowResult


def analyze_line_stress(
    grid: GridModel,
    result: PowerFlowResult,
    thresholds: StressThresholds,
) -> list[LineStress]:
    lines_by_id = {line.id: line for line in grid.lines}
    stresses: list[LineStress] = []
    for line_result in result.lines:
        status, severity = classify_line(
            line_result.loading_percentage, thresholds
        )
        line = lines_by_id.get(line_result.line_id)
        stresses.append(
            LineStress(
                line_id=line_result.line_id,
                line_name=line.name if line else "",
                from_bus=line_result.from_bus,
                to_bus=line_result.to_bus,
                loading_percentage=round(line_result.loading_percentage, 1),
                thermal_limit=line.thermal_limit if line else 0.0,
                status=status,
                severity=severity,
                margin_remaining=round(
                    thresholds.line_overload_threshold
                    - line_result.loading_percentage,
                    1,
                ),
            )
        )
    return stresses


def worst_line_severity(stresses: list[LineStress]) -> SeverityLevel:
    if any(stress.severity == SeverityLevel.CRITICAL for stress in stresses):
        return SeverityLevel.CRITICAL
    if any(stress.severity == SeverityLevel.WARNING for stress in stresses):
        return SeverityLevel.WARNING
    return SeverityLevel.NORMAL
