"""Pure constraint classification helpers used by every stress detector.

These functions convert a raw measured value (voltage pu or line loading %)
into a classification and a severity using the configured thresholds. They
contain no business logic beyond the classification rules.
"""

from app.config.thresholds import StressThresholds
from app.domain.enums import SeverityLevel, VoltageClass
from app.power_system.results import LineStatus


def classify_voltage(
    voltage_pu: float,
    thresholds: StressThresholds,
) -> tuple[VoltageClass, SeverityLevel]:
    if (
        voltage_pu < thresholds.voltage_critical_low
        or voltage_pu > thresholds.voltage_critical_high
    ):
        classification = (
            VoltageClass.UNDER_VOLTAGE
            if voltage_pu < thresholds.voltage_critical_low
            else VoltageClass.OVER_VOLTAGE
        )
        return classification, SeverityLevel.CRITICAL
    if (
        voltage_pu < thresholds.voltage_warning_low
        or voltage_pu > thresholds.voltage_warning_high
    ):
        classification = (
            VoltageClass.UNDER_VOLTAGE
            if voltage_pu < thresholds.voltage_warning_low
            else VoltageClass.OVER_VOLTAGE
        )
        return classification, SeverityLevel.WARNING
    return VoltageClass.NORMAL, SeverityLevel.NORMAL


def voltage_deviation_from_limit(
    voltage_pu: float,
    classification: VoltageClass,
    thresholds: StressThresholds,
) -> float:
    if classification == VoltageClass.OVER_VOLTAGE:
        return max(0.0, voltage_pu - thresholds.voltage_normal_high)
    if classification == VoltageClass.UNDER_VOLTAGE:
        return max(0.0, thresholds.voltage_normal_low - voltage_pu)
    return 0.0


def classify_line(
    loading_percentage: float,
    thresholds: StressThresholds,
) -> tuple[LineStatus, SeverityLevel]:
    if loading_percentage > thresholds.line_overload_threshold:
        return LineStatus.OVERLOADED, SeverityLevel.CRITICAL
    if loading_percentage >= thresholds.line_warning_threshold:
        return LineStatus.WARNING, SeverityLevel.WARNING
    return LineStatus.NORMAL, SeverityLevel.NORMAL
