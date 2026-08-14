"""Grid stress analysis: composes the individual detectors into a unified
stress result with a transparent, configurable stress score and a unified
Issue list.

The pipeline is:

    PowerFlowResult -> Constraint Analysis -> Stress Detection
        -> Issue Classification -> Stress Score
"""

from app.config.thresholds import StressThresholds, stress_thresholds
from app.domain.enums import (
    BusType,
    GenerationDetection,
    ImpactLevel,
    IssueCategory,
    SeverityLevel,
    StressLevel,
)
from app.domain.models import GridModel
from app.domain.stress_models import (
    BusStress,
    GenerationBalance,
    LineStress,
    RenewableImpact,
    StressAnalysisResult,
    StressComponentScore,
    StressIssue,
    StressScore,
)
from app.power_system.generation_analysis import analyze_generation_balance
from app.power_system.line_analysis import analyze_line_stress
from app.power_system.results import PowerFlowResult
from app.power_system.voltage_analysis import analyze_voltage_stress

_VIOLATION_CATEGORIES = (IssueCategory.VOLTAGE_STRESS, IssueCategory.TRANSMISSION_STRESS)


def _violation_fingerprint(issue: StressIssue) -> tuple[str, str, str]:
    return (issue.category.value, issue.affected_component_type, issue.affected_component_id or "")


def analyze_renewable_impact(
    grid: GridModel,
    result: PowerFlowResult,
    issues: list[StressIssue],
    thresholds: StressThresholds,
    baseline: StressAnalysisResult | None = None,
) -> RenewableImpact:
    summary = result.summary
    renewable_mw = summary.renewable_generation_mw if summary else 0.0
    total_load = summary.total_load_mw if summary else 0.0
    penetration = renewable_mw / total_load * 100.0 if total_load > 0 else 0.0

    if baseline is not None:
        baseline_set = {
            _violation_fingerprint(issue)
            for issue in baseline.issues
            if issue.category in _VIOLATION_CATEGORIES
        }
        current_set = {
            _violation_fingerprint(issue)
            for issue in issues
            if issue.category in _VIOLATION_CATEGORIES
        }
        new_violations = [
            f"{category}:{component_type}:{component}"
            for category, component_type, component in sorted(current_set - baseline_set)
        ]
        resolved_violations = [
            f"{category}:{component_type}:{component}"
            for category, component_type, component in sorted(baseline_set - current_set)
        ]

        if not new_violations and not resolved_violations:
            level = ImpactLevel.NEUTRAL
            reason = "Renewable scenario introduced no new violations and resolved none."
        elif not new_violations and resolved_violations:
            level = ImpactLevel.POSITIVE
            reason = (
                f"Renewable scenario resolved {len(resolved_violations)} violation(s) "
                "without introducing new ones."
            )
        elif new_violations and not resolved_violations:
            level = ImpactLevel.HIGH_RISK
            reason = (
                f"Renewable scenario introduced {len(new_violations)} new violation(s) "
                "without resolving any."
            )
        else:
            level = ImpactLevel.NEGATIVE
            reason = (
                f"Renewable scenario introduced {len(new_violations)} new violation(s) "
                f"while resolving {len(resolved_violations)}."
            )
        return RenewableImpact(
            renewable_penetration=round(penetration, 1),
            renewable_generation_mw=round(renewable_mw, 1),
            impact_level=level,
            new_violations=new_violations,
            resolved_violations=resolved_violations,
            reason=reason,
        )

    if renewable_mw <= 0:
        return RenewableImpact(
            renewable_penetration=0.0,
            renewable_generation_mw=0.0,
            impact_level=ImpactLevel.NEUTRAL,
            reason="No renewable generation present in this analysis.",
        )

    current = [issue for issue in issues if issue.category in _VIOLATION_CATEGORIES]
    critical = any(issue.severity == SeverityLevel.CRITICAL for issue in current)
    if not current:
        level = ImpactLevel.POSITIVE
        reason = "Renewable generation integrated without introducing violations."
    elif critical:
        level = ImpactLevel.HIGH_RISK
        reason = (
            f"Renewable penetration of {penetration:.1f}% coexists with critical "
            "voltage or line violations."
        )
    else:
        level = ImpactLevel.NEGATIVE
        reason = (
            f"Renewable penetration of {penetration:.1f}% coexists with "
            f"{len(current)} voltage or line violation(s)."
        )
    return RenewableImpact(
        renewable_penetration=round(penetration, 1),
        renewable_generation_mw=round(renewable_mw, 1),
        impact_level=level,
        reason=reason,
    )


def _severity_points(severity: SeverityLevel, thresholds: StressThresholds) -> float:
    if severity == SeverityLevel.CRITICAL:
        return thresholds.severity_critical_points
    if severity == SeverityLevel.WARNING:
        return thresholds.severity_warning_points
    return 0.0


def _bus_label(bus: BusStress) -> str:
    return f"{bus.bus_id} {bus.bus_name}".strip() or bus.bus_id


def _line_label(line: LineStress) -> str:
    return f"{line.line_id} {line.line_name}".strip() or line.line_id


def voltage_component(
    buses: list[BusStress], thresholds: StressThresholds
) -> StressComponentScore:
    affected = [bus for bus in buses if bus.severity != SeverityLevel.NORMAL]
    if not affected:
        return StressComponentScore(
            key="voltage",
            label="Voltage",
            score=0.0,
            reason="All bus voltages are within the normal band.",
        )
    worst = max(_severity_points(bus.severity, thresholds) for bus in affected)
    extra = min(
        thresholds.voltage_extra_per_bus * (len(affected) - 1),
        thresholds.voltage_extra_cap,
    )
    score = min(100.0, worst + extra)
    worst_bus = max(affected, key=lambda bus: _severity_points(bus.severity, thresholds))
    reason = (
        f"Worst voltage stress at {_bus_label(worst_bus)}: "
        f"{worst_bus.voltage_pu:.3f} pu "
        f"({worst_bus.classification.value}, {worst_bus.severity.value}). "
        f"{len(affected)} bus(es) outside the normal band."
    )
    return StressComponentScore(
        key="voltage", label="Voltage", score=round(score, 1), reason=reason
    )


def transmission_component(
    lines: list[LineStress], thresholds: StressThresholds
) -> StressComponentScore:
    affected = [line for line in lines if line.severity != SeverityLevel.NORMAL]
    if not affected:
        return StressComponentScore(
            key="transmission",
            label="Transmission",
            score=0.0,
            reason="All lines are below the warning loading threshold.",
        )
    worst = max(_severity_points(line.severity, thresholds) for line in affected)
    extra = min(
        thresholds.line_extra_per_line * (len(affected) - 1),
        thresholds.line_extra_cap,
    )
    score = min(100.0, worst + extra)
    worst_line = max(affected, key=lambda line: _severity_points(line.severity, thresholds))
    reason = (
        f"Worst loading on {_line_label(worst_line)}: "
        f"{worst_line.loading_percentage:.1f}% ({worst_line.status.value}). "
        f"{len(affected)} line(s) at or above the warning threshold."
    )
    return StressComponentScore(
        key="transmission", label="Transmission", score=round(score, 1), reason=reason
    )


def generation_component(
    generation: GenerationBalance, thresholds: StressThresholds
) -> StressComponentScore:
    detections = generation.detections
    if not detections:
        return StressComponentScore(
            key="generation",
            label="Generation",
            score=0.0,
            reason="Generation balances load; no generator is at its configured limit.",
        )
    score = 0.0
    reasons: list[str] = []
    if GenerationDetection.GENERATION_INSUFFICIENT in detections:
        score = max(score, 70.0)
        reasons.append(
            f"Slack output {generation.slack_generation_mw:.1f} MW is at/near its "
            f"{generation.slack_max_mw:.1f} MW maximum."
        )
    if GenerationDetection.EXCESS_GENERATION in detections:
        score = max(score, 70.0)
        reasons.append(
            f"Slack output {generation.slack_generation_mw:.1f} MW is negative, "
            "indicating excess generation."
        )
    if GenerationDetection.IMBALANCED_SYSTEM in detections:
        score = max(score, 60.0)
        reasons.append(
            f"System relies heavily on the slack bus "
            f"({generation.slack_generation_mw:.1f} MW of "
            f"{generation.total_generation_mw:.1f} MW total)."
        )
    if GenerationDetection.GENERATOR_AT_LIMIT in detections:
        at_limit = 40.0 + 10.0 * min(len(generation.generators_at_limit), 3)
        score = max(score, min(at_limit, 70.0))
        reasons.append(
            f"Generator(s) at configured limits: {', '.join(generation.generators_at_limit)}."
        )
    return StressComponentScore(
        key="generation",
        label="Generation",
        score=round(min(score, 100.0), 1),
        reason=" ".join(reasons),
    )


def renewable_component(renewable: RenewableImpact) -> StressComponentScore:
    mapping = {
        ImpactLevel.POSITIVE: 10.0,
        ImpactLevel.NEUTRAL: 0.0,
        ImpactLevel.NEGATIVE: 60.0,
        ImpactLevel.HIGH_RISK: 100.0,
    }
    score = mapping.get(renewable.impact_level, 0.0)
    return StressComponentScore(
        key="renewable",
        label="Renewable Impact",
        score=score,
        reason=renewable.reason or "No renewable impact detected.",
    )


def compute_stress_score(
    buses: list[BusStress],
    lines: list[LineStress],
    generation: GenerationBalance,
    renewable: RenewableImpact,
    thresholds: StressThresholds,
) -> StressScore:
    components = [
        voltage_component(buses, thresholds),
        transmission_component(lines, thresholds),
        generation_component(generation, thresholds),
        renewable_component(renewable),
    ]
    weights = thresholds.score_weights
    total = sum(
        component.score * weights.get(component.key, 0.0) for component in components
    )
    overall = round(total, 1)

    if overall < thresholds.low_score_max:
        classification = StressLevel.LOW
    elif overall < thresholds.moderate_score_max:
        classification = StressLevel.MODERATE
    elif overall < thresholds.high_score_max:
        classification = StressLevel.HIGH
    else:
        classification = StressLevel.CRITICAL

    reasons = [component.reason for component in components if component.score > 0]
    reasons.insert(
        0,
        f"Stress score is {classification.value} "
        f"({overall}/100) from {len(reasons)} contributing component(s).",
    )
    return StressScore(
        overall_score=overall,
        classification=classification,
        components=components,
        reasons=reasons,
    )


def _build_issues(
    buses: list[BusStress],
    lines: list[LineStress],
    generation: GenerationBalance,
    renewable: RenewableImpact,
    thresholds: StressThresholds,
) -> list[StressIssue]:
    issues: list[StressIssue] = []
    counter = 0

    def next_id() -> str:
        nonlocal counter
        counter += 1
        return f"issue_{counter:03d}"

    for bus in buses:
        if bus.severity == SeverityLevel.NORMAL:
            continue
        if bus.classification.value == "UNDER_VOLTAGE":
            title = "Bus undervoltage"
            description = f"Bus voltage {bus.voltage_pu:.3f} pu is below the configured lower limit."
        else:
            title = "Bus overvoltage"
            description = f"Bus voltage {bus.voltage_pu:.3f} pu exceeds the configured upper limit."
        issues.append(
            StressIssue(
                id=next_id(),
                category=IssueCategory.VOLTAGE_STRESS,
                severity=bus.severity,
                affected_component_type="BUS",
                affected_component_id=bus.bus_id,
                title=title,
                description=description,
                evidence={
                    "voltage_pu": bus.voltage_pu,
                    "deviation_from_nominal": bus.deviation_from_nominal,
                    "deviation_from_limit": bus.deviation_from_limit,
                    "normal_low": thresholds.voltage_normal_low,
                    "normal_high": thresholds.voltage_normal_high,
                },
            )
        )

    for line in lines:
        if line.severity == SeverityLevel.NORMAL:
            continue
        if line.severity == SeverityLevel.CRITICAL:
            title = "Transmission line overloaded"
            description = "Line loading exceeds its configured thermal limit."
            evidence = {
                "loading_percentage": line.loading_percentage,
                "limit_percentage": thresholds.line_overload_threshold,
            }
        else:
            title = "Transmission line loading warning"
            description = "Line loading is approaching its configured thermal limit."
            evidence = {
                "loading_percentage": line.loading_percentage,
                "warning_threshold": thresholds.line_warning_threshold,
            }
        issues.append(
            StressIssue(
                id=next_id(),
                category=IssueCategory.TRANSMISSION_STRESS,
                severity=line.severity,
                affected_component_type="LINE",
                affected_component_id=line.line_id,
                title=title,
                description=description,
                evidence=evidence,
            )
        )

    if GenerationDetection.GENERATION_INSUFFICIENT in generation.detections:
        issues.append(
            StressIssue(
                id=next_id(),
                category=IssueCategory.GENERATION_BALANCE,
                severity=SeverityLevel.CRITICAL,
                affected_component_type="SYSTEM",
                title="Generation may be insufficient",
                description="Available generation is at or near its maximum capacity.",
                evidence={
                    "slack_generation_mw": generation.slack_generation_mw,
                    "slack_max_mw": generation.slack_max_mw,
                },
            )
        )
    if GenerationDetection.EXCESS_GENERATION in generation.detections:
        issues.append(
            StressIssue(
                id=next_id(),
                category=IssueCategory.GENERATION_BALANCE,
                severity=SeverityLevel.CRITICAL,
                affected_component_type="SYSTEM",
                title="Excess generation detected",
                description="The slack bus is absorbing power, indicating surplus generation.",
                evidence={
                    "slack_generation_mw": generation.slack_generation_mw,
                },
            )
        )
    if GenerationDetection.IMBALANCED_SYSTEM in generation.detections:
        issues.append(
            StressIssue(
                id=next_id(),
                category=IssueCategory.GENERATION_BALANCE,
                severity=SeverityLevel.CRITICAL,
                affected_component_type="SYSTEM",
                title="Generation imbalance",
                description="The system depends heavily on the slack bus to balance.",
                evidence={
                    "slack_generation_mw": generation.slack_generation_mw,
                    "total_generation_mw": generation.total_generation_mw,
                },
            )
        )
    if GenerationDetection.GENERATOR_AT_LIMIT in generation.detections:
        issues.append(
            StressIssue(
                id=next_id(),
                category=IssueCategory.GENERATION_BALANCE,
                severity=SeverityLevel.WARNING,
                affected_component_type="GENERATOR",
                affected_component_id=(
                    generation.generators_at_limit[0]
                    if generation.generators_at_limit
                    else None
                ),
                title="Generator operating at limit",
                description="One or more generators operate at their configured active-power limits.",
                evidence={
                    "generators_at_limit": ",".join(generation.generators_at_limit),
                },
            )
        )

    if renewable.impact_level in (ImpactLevel.NEGATIVE, ImpactLevel.HIGH_RISK):
        issues.append(
            StressIssue(
                id=next_id(),
                category=IssueCategory.RENEWABLE_IMPACT,
                severity=(
                    SeverityLevel.CRITICAL
                    if renewable.impact_level == ImpactLevel.HIGH_RISK
                    else SeverityLevel.WARNING
                ),
                affected_component_type="SYSTEM",
                title="Renewable integration impact",
                description=renewable.reason,
                evidence={
                    "renewable_penetration": renewable.renewable_penetration,
                    "new_violations": len(renewable.new_violations),
                    "resolved_violations": len(renewable.resolved_violations),
                },
            )
        )

    return issues


def build_stress_analysis(
    *,
    analysis_id: str,
    grid_id: str,
    grid: GridModel,
    result: PowerFlowResult,
    thresholds: StressThresholds = stress_thresholds,
    baseline: StressAnalysisResult | None = None,
) -> StressAnalysisResult:
    buses = analyze_voltage_stress(grid, result, thresholds)
    lines = analyze_line_stress(grid, result, thresholds)
    generation = analyze_generation_balance(grid, result, thresholds)

    core_issues = _build_issues(buses, lines, generation, RenewableImpact(
        renewable_penetration=0.0,
        renewable_generation_mw=0.0,
        impact_level=ImpactLevel.NEUTRAL,
    ), thresholds)
    renewable = analyze_renewable_impact(grid, result, core_issues, thresholds, baseline)
    issues = _build_issues(buses, lines, generation, renewable, thresholds)
    score = compute_stress_score(buses, lines, generation, renewable, thresholds)

    return StressAnalysisResult(
        analysis_id=analysis_id,
        grid_id=grid_id,
        score=score,
        buses=buses,
        lines=lines,
        generation=generation,
        renewable=renewable,
        issues=issues,
    )
