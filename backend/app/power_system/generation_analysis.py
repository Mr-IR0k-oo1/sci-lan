"""Generation balance analysis based on the power-flow result.

Only quantities the model actually supports are calculated. Reserve is derived
from the configured `active_power_max` headroom of each generator; no reserve
data is fabricated. The slack generator absorbs the net imbalance, so its
computed output is the primary signal for insufficiency / excess generation.
"""

from app.config.thresholds import StressThresholds
from app.domain.enums import BusType, GenerationDetection, SeverityLevel
from app.domain.models import GridModel
from app.domain.stress_models import GenerationBalance
from app.power_system.results import PowerFlowResult


def _slack_output(grid: GridModel, result: PowerFlowResult) -> tuple[float, float, str]:
    slack = next(bus for bus in grid.buses if bus.type == BusType.SLACK)
    slack_max = 0.0
    for generator in grid.generators:
        if generator.bus_id == slack.id:
            slack_max = generator.active_power_max
            break
    slack_bus_result = next(
        (bus_result for bus_result in result.buses if bus_result.bus_id == slack.id),
        None,
    )
    output = slack_bus_result.active_power if slack_bus_result else 0.0
    return output, slack_max, slack.id


def analyze_generation_balance(
    grid: GridModel,
    result: PowerFlowResult,
    thresholds: StressThresholds,
) -> GenerationBalance:
    summary = result.summary
    if summary is None:
        return GenerationBalance(
            total_generation_mw=0.0,
            total_load_mw=0.0,
            total_losses_mw=0.0,
            slack_generation_mw=0.0,
            slack_max_mw=0.0,
            available_reserve_mw=0.0,
            renewable_generation_mw=0.0,
            status="NOT_CONVERGED",
            severity=SeverityLevel.NORMAL,
        )

    slack_output, slack_max, slack_id = _slack_output(grid, result)
    epsilon = thresholds.generator_limit_epsilon_mw
    detections: list[GenerationDetection] = []
    generators_at_limit: list[str] = []

    for generator in grid.generators:
        if generator.bus_id == slack_id:
            continue
        near_min = generator.active_power - generator.active_power_min <= epsilon
        near_max = generator.active_power_max - generator.active_power <= epsilon
        if near_min or near_max:
            generators_at_limit.append(generator.id)

    reserve = sum(
        max(generator.active_power_max - generator.active_power, 0.0)
        for generator in grid.generators
        if generator.bus_id != slack_id
    )
    if slack_max > 0:
        reserve += max(slack_max - slack_output, 0.0)

    if slack_output < thresholds.excess_generation_threshold_mw:
        detections.append(GenerationDetection.EXCESS_GENERATION)
    if summary.total_generation_mw < summary.total_load_mw - epsilon:
        detections.append(GenerationDetection.GENERATION_INSUFFICIENT)
    if slack_max > 0 and slack_output >= slack_max * thresholds.insufficient_slack_fraction:
        detections.append(GenerationDetection.GENERATION_INSUFFICIENT)
    if generators_at_limit:
        detections.append(GenerationDetection.GENERATOR_AT_LIMIT)
    if slack_max > 0 and slack_output >= slack_max * thresholds.insufficient_slack_fraction:
        detections.append(GenerationDetection.IMBALANCED_SYSTEM)
    elif summary.total_generation_mw > 0 and (
        slack_output / summary.total_generation_mw
    ) >= thresholds.slack_reliance_threshold:
        detections.append(GenerationDetection.IMBALANCED_SYSTEM)

    severity = SeverityLevel.NORMAL
    if any(
        detection in (
            GenerationDetection.GENERATION_INSUFFICIENT,
            GenerationDetection.EXCESS_GENERATION,
            GenerationDetection.IMBALANCED_SYSTEM,
        )
        for detection in detections
    ):
        severity = SeverityLevel.CRITICAL
    elif GenerationDetection.GENERATOR_AT_LIMIT in detections:
        severity = SeverityLevel.WARNING

    status = ", ".join(detection.value for detection in detections) if detections else "BALANCED"

    return GenerationBalance(
        total_generation_mw=round(summary.total_generation_mw, 2),
        total_load_mw=round(summary.total_load_mw, 2),
        total_losses_mw=round(summary.total_losses_mw, 2),
        slack_generation_mw=round(slack_output, 2),
        slack_max_mw=round(slack_max, 2),
        available_reserve_mw=round(reserve, 2),
        renewable_generation_mw=round(summary.renewable_generation_mw, 2),
        detections=detections,
        generators_at_limit=generators_at_limit,
        status=status,
        severity=severity,
    )
