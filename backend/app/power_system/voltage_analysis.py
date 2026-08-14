"""Voltage stress detection across all buses of an analyzed grid."""

from app.config.thresholds import StressThresholds
from app.domain.enums import SeverityLevel, VoltageClass
from app.domain.models import GridModel
from app.domain.stress_models import BusStress
from app.power_system.constraints import (
    classify_voltage,
    voltage_deviation_from_limit,
)
from app.power_system.results import PowerFlowResult


def analyze_voltage_stress(
    grid: GridModel,
    result: PowerFlowResult,
    thresholds: StressThresholds,
) -> list[BusStress]:
    buses_by_id = {bus.id: bus for bus in grid.buses}
    stresses: list[BusStress] = []
    for bus_result in result.buses:
        classification, severity = classify_voltage(
            bus_result.voltage_magnitude, thresholds
        )
        bus = buses_by_id.get(bus_result.bus_id)
        stresses.append(
            BusStress(
                bus_id=bus_result.bus_id,
                bus_name=bus.name if bus else "",
                voltage_pu=round(bus_result.voltage_magnitude, 4),
                classification=classification,
                severity=severity,
                deviation_from_nominal=round(
                    abs(bus_result.voltage_magnitude - 1.0), 4
                ),
                deviation_from_limit=round(
                    voltage_deviation_from_limit(
                        bus_result.voltage_magnitude, classification, thresholds
                    ),
                    4,
                ),
            )
        )
    return stresses


def worst_voltage_severity(stresses: list[BusStress]) -> SeverityLevel:
    if any(stress.severity == SeverityLevel.CRITICAL for stress in stresses):
        return SeverityLevel.CRITICAL
    if any(stress.severity == SeverityLevel.WARNING for stress in stresses):
        return SeverityLevel.WARNING
    return SeverityLevel.NORMAL
