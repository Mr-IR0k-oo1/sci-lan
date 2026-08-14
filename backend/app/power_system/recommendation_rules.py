"""Recommendation rules: map stress conditions to prioritized recommendations.

Each rule produces a Recommendation with a severity-derived priority and a
category, so the front-end can render the top-level action list without
re-deriving it from the raw issues.
"""

from app.config.thresholds import StressThresholds, stress_thresholds
from app.domain.enums import (
    ConfidenceLevel,
    GenerationDetection,
    ImpactLevel,
    IssueCategory,
    RecommendationPriority,
    SeverityLevel,
)
from app.domain.recommendation_models import Recommendation
from app.domain.stress_models import StressAnalysisResult


class RecommendationRule:
    def __init__(
        self,
        rule_id: str,
        category: str,
        title: str,
        description: str,
        severity: SeverityLevel,
        suggested_actions: list[str],
        expected_effect: list[str],
    ) -> None:
        self.rule_id = rule_id
        self.category = category
        self.title = title
        self.description = description
        self.severity = severity
        self.suggested_actions = suggested_actions
        self.expected_effect = expected_effect

    @property
    def priority(self) -> RecommendationPriority:
        if self.severity == SeverityLevel.CRITICAL:
            return RecommendationPriority.HIGH
        if self.severity == SeverityLevel.WARNING:
            return RecommendationPriority.MEDIUM
        return RecommendationPriority.LOW

    @property
    def confidence(self) -> ConfidenceLevel:
        if self.severity == SeverityLevel.CRITICAL:
            return ConfidenceLevel.HIGH
        return ConfidenceLevel.MEDIUM


def _has_detection(results: list[StressAnalysisResult], detection: GenerationDetection) -> bool:
    return any(detection in result.generation.detections for result in results)


def _generator_ids(results: list[StressAnalysisResult]) -> list[str]:
    seen: list[str] = []
    for result in results:
        for generator in result.generation.generators_at_limit:
            if generator not in seen:
                seen.append(generator)
    return seen


def evaluate_rules(
    results: list[StressAnalysisResult],
    thresholds: StressThresholds = stress_thresholds,
) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    counter = 0

    def add(rule: RecommendationRule, related_issue_ids: list[str]) -> None:
        nonlocal counter
        counter += 1
        recommendations.append(
            Recommendation(
                id=f"rec_{counter:03d}",
                title=rule.title,
                category=rule.category,
                priority=rule.priority,
                description=rule.description,
                reason=rule.description,
                related_issue_ids=related_issue_ids,
                suggested_actions=rule.suggested_actions,
                expected_effect=rule.expected_effect,
                confidence=rule.confidence,
            )
        )

    # --- Voltage -------------------------------------------------------------
    over_issues = [
        issue
        for result in results
        for issue in result.issues
        if issue.category == IssueCategory.VOLTAGE_STRESS
        and issue.title == "Bus overvoltage"
        and issue.affected_component_id
    ]
    under_issues = [
        issue
        for result in results
        for issue in result.issues
        if issue.category == IssueCategory.VOLTAGE_STRESS
        and issue.title == "Bus undervoltage"
        and issue.affected_component_id
    ]
    over_buses = sorted({issue.affected_component_id for issue in over_issues})
    under_buses = sorted({issue.affected_component_id for issue in under_issues})

    if over_buses:
        add(
            RecommendationRule(
                "VOLTAGE_REDUCE_GENERATION",
                "voltage",
                "Reduce reactive injection near high-voltage buses",
                "Reduce reactive power injection (shunt capacitors or over-excited "
                f"generators) at or near buses: {', '.join(over_buses)}.",
                SeverityLevel.CRITICAL,
                [
                    "Reduce generator voltage setpoints near overvoltage buses.",
                    "Disconnect shunt capacitor banks at the affected buses.",
                ],
                ["Bring the affected bus voltages back into the normal band."],
            ),
            [issue.id for issue in over_issues],
        )
    if under_buses:
        add(
            RecommendationRule(
                "VOLTAGE_ADD_CAPACITORS",
                "voltage",
                "Add shunt compensation to support voltage",
                "Add shunt capacitors or adjust transformer taps to raise voltage at "
                f"buses: {', '.join(under_buses)}.",
                SeverityLevel.CRITICAL,
                [
                    "Install shunt capacitor banks at the affected buses.",
                    "Raise transformer tap positions to boost voltage support.",
                ],
                ["Raise the affected bus voltages back into the normal band."],
            ),
            [issue.id for issue in under_issues],
        )

    # --- Transmission ----------------------------------------------------------
    overloaded_issues = [
        issue
        for result in results
        for issue in result.issues
        if issue.category == IssueCategory.TRANSMISSION_STRESS
        and issue.title == "Transmission line overloaded"
        and issue.affected_component_id
    ]
    warned_issues = [
        issue
        for result in results
        for issue in result.issues
        if issue.category == IssueCategory.TRANSMISSION_STRESS
        and issue.title == "Transmission line loading warning"
        and issue.affected_component_id
    ]
    overloaded_lines = sorted({issue.affected_component_id for issue in overloaded_issues})
    warned_lines = sorted({issue.affected_component_id for issue in warned_issues})

    if overloaded_lines:
        add(
            RecommendationRule(
                "REDUCE_LOAD_ON_OVERLOADED_LINES",
                "transmission",
                "Reduce load on overloaded transmission lines",
                "Dispatch generation or curtail load to reduce flow on overloaded lines: "
                f"{', '.join(overloaded_lines)}.",
                SeverityLevel.CRITICAL,
                [
                    "Redispatch generation to reduce power transfer on the affected lines.",
                    "Curtail the most sensitive loads connected behind the affected lines.",
                ],
                ["Bring line loading below the configured thermal limit."],
            ),
            [issue.id for issue in overloaded_issues],
        )
    elif warned_lines:
        add(
            RecommendationRule(
                "MONITOR_WARNED_LINES",
                "transmission",
                "Monitor transmission lines approaching limits",
                "Dispatch generation to reduce flow on lines approaching their thermal "
                f"limit: {', '.join(warned_lines)}.",
                SeverityLevel.WARNING,
                [
                    "Redispatch generation to reduce loading on the warned lines.",
                ],
                ["Prevent the warned lines from reaching their thermal limit."],
            ),
            [issue.id for issue in warned_issues],
        )

    # --- Generation ------------------------------------------------------------
    if _has_detection(results, GenerationDetection.GENERATION_INSUFFICIENT):
        add(
            RecommendationRule(
                "INCREASE_GENERATION_CAPACITY",
                "generation",
                "Increase generation capacity",
                "Available generation is at or near its maximum. Add generation capacity "
                "or curtail load to restore operating headroom.",
                SeverityLevel.CRITICAL,
                [
                    "Commit additional generation units.",
                    "Curtail load to restore reserve headroom.",
                ],
                ["Restore reserve headroom and keep the slack bus below its limit."],
            ),
            [
                issue.id
                for result in results
                for issue in result.issues
                if issue.title == "Generation may be insufficient"
            ],
        )
    if _has_detection(results, GenerationDetection.EXCESS_GENERATION):
        add(
            RecommendationRule(
                "CURTAIL_EXCESS_GENERATION",
                "generation",
                "Curtail excess generation",
                "The slack bus is absorbing power, indicating surplus generation. "
                "Curtail generation to bring the system back into balance.",
                SeverityLevel.CRITICAL,
                [
                    "Decrease output of the largest generators.",
                    "Increase storage charging where available.",
                ],
                ["Bring the slack bus output back to a balanced value."],
            ),
            [
                issue.id
                for result in results
                for issue in result.issues
                if issue.title == "Excess generation detected"
            ],
        )
    if _has_detection(results, GenerationDetection.IMBALANCED_SYSTEM):
        add(
            RecommendationRule(
                "REDISTRIBUTE_GENERATION",
                "generation",
                "Redistribute generation across the system",
                "The system depends heavily on the slack bus. Redistribute generation to "
                "reduce the slack share.",
                SeverityLevel.CRITICAL,
                [
                    "Raise output of non-slack generators.",
                    "Lower output of the slack generator to match.",
                ],
                ["Reduce the slack share of total generation."],
            ),
            [
                issue.id
                for result in results
                for issue in result.issues
                if issue.title == "Generation imbalance"
            ],
        )
    if _has_detection(results, GenerationDetection.GENERATOR_AT_LIMIT):
        add(
            RecommendationRule(
                "REVIEW_GENERATOR_LIMITS",
                "generation",
                "Review generator operating limits",
                f"Generators at their configured limits: {', '.join(_generator_ids(results))}.",
                SeverityLevel.WARNING,
                [
                    "Verify the operating limits of the listed generators.",
                    "Review whether dispatch can be redistributed to other units.",
                ],
                ["Prevent generators from persistently operating at their limits."],
            ),
            [
                issue.id
                for result in results
                for issue in result.issues
                if issue.title == "Generator operating at limit"
            ],
        )

    # --- Renewable impact ---------------------------------------------------------
    impact_rank = {
        ImpactLevel.NEUTRAL: 0,
        ImpactLevel.POSITIVE: 1,
        ImpactLevel.NEGATIVE: 2,
        ImpactLevel.HIGH_RISK: 3,
    }
    worst_renewable = max(
        (result.renewable.impact_level for result in results),
        key=lambda level: impact_rank[level],
    )
    if worst_renewable in (ImpactLevel.NEGATIVE, ImpactLevel.HIGH_RISK):
        add(
            RecommendationRule(
                "ADD_STORAGE_OR_STABILITY_CONTROLS",
                "renewable",
                "Add storage or stability controls for renewable integration",
                "Renewable integration introduces or worsens violations. Add storage, "
                "curtailment, or grid-stability controls.",
                SeverityLevel.CRITICAL
                if worst_renewable == ImpactLevel.HIGH_RISK
                else SeverityLevel.WARNING,
                [
                    "Add battery storage to smooth renewable output.",
                    "Add automatic curtailment for the worst renewable injections.",
                ],
                ["Neutralize new violations introduced by renewable integration."],
            ),
            [
                issue.id
                for result in results
                for issue in result.issues
                if issue.category == IssueCategory.RENEWABLE_IMPACT
            ],
        )

    # CRITICAL before WARNING, stable by id within a tier.
    order = {RecommendationPriority.HIGH: 0, RecommendationPriority.MEDIUM: 1, RecommendationPriority.LOW: 2}
    recommendations.sort(key=lambda rec: (order[rec.priority], rec.id))
    return recommendations
