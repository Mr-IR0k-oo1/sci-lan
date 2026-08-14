"""Stress analysis service: orchestrates power flow, stress analysis,
recommendation generation, and mitigation simulation for a grid.

The pipeline mirrors the analysis-record model:

    grid -> power flow -> AnalysisRecord
        -> stress analysis (voltage, line, generation, renewable)
        -> recommendations (rules)
        -> mitigation candidates -> mitigation tests (re-run power flow)
"""

from __future__ import annotations

from app.core.config import Settings, settings as default_settings
from app.domain.enums import GeneratorType, IssueCategory
from app.domain.models import GridModel
from app.domain.recommendation_models import (
    AnalysisRecord,
    MetricChange,
    MitigationCandidate,
    MitigationModification,
    MitigationTestResult,
)
from app.power_system.recommendation_rules import evaluate_rules
from app.power_system.results import PowerFlowSummary
from app.power_system.stress import build_stress_analysis
from app.services import analysis_history_service, grid_service, power_flow_service


def run_full_analysis(
    grid_id: str,
    tolerance: float | None = None,
    max_iterations: int | None = None,
    engine_name: str | None = None,
    settings: Settings = default_settings,
) -> AnalysisRecord:
    grid = grid_service.get_grid(grid_id)
    result = power_flow_service.run_power_flow(
        grid,
        tolerance=tolerance,
        max_iterations=max_iterations,
        engine_name=engine_name,
        settings=settings,
    )
    record = analysis_history_service.record_analysis(grid, result)
    record.stress = build_stress_analysis(
        analysis_id=record.id,
        grid_id=grid.grid_id,
        grid=grid,
        result=result,
    )
    record.recommendations = evaluate_rules([record.stress])
    record.mitigation_candidates = build_mitigation_candidates(record)
    return record


def run_comparative_analysis(
    analysis_id: str,
    grid_id: str | None = None,
    tolerance: float | None = None,
    max_iterations: int | None = None,
    engine_name: str | None = None,
    settings: Settings = default_settings,
) -> AnalysisRecord:
    baseline = analysis_history_service.get_analysis(analysis_id)
    grid_id = grid_id or baseline.grid_id
    return run_full_analysis(
        grid_id,
        tolerance=tolerance,
        max_iterations=max_iterations,
        engine_name=engine_name,
        settings=settings,
    )


def _apply_modification(
    grid: GridModel, modification: MitigationModification
) -> GridModel:
    if modification.type == "GENERATOR_OUTPUT":
        generators = []
        for generator in grid.generators:
            updated = generator
            if generator.id == modification.generator_id:
                updated = generator.model_copy(
                    update={"active_power": modification.new_value}
                )
            generators.append(updated)
        return grid.model_copy(update={"generators": generators})

    if modification.type == "LOAD_CURTAILMENT":
        loads = []
        for load in grid.loads:
            updated = load
            if load.id == modification.load_id:
                scale = max(0.0, modification.new_value) / max(load.active_power, 1e-9)
                updated = load.model_copy(
                    update={
                        "active_power": modification.new_value,
                        "reactive_power": load.reactive_power * scale,
                    }
                )
            loads.append(updated)
        return grid.model_copy(update={"loads": loads})

    if modification.type == "GENERATOR_SHUNT_REACTIVE":
        generators = []
        for generator in grid.generators:
            updated = generator
            if generator.id == modification.generator_id:
                updated = generator.model_copy(
                    update={"reactive_power": modification.new_value}
                )
            generators.append(updated)
        return grid.model_copy(update={"generators": generators})

    return grid


def build_mitigation_candidates(
    record: AnalysisRecord,
) -> list[MitigationCandidate]:
    candidates: list[MitigationCandidate] = []
    if not record.stress:
        return candidates

    bus_by_id = {bus.id: bus for bus in record.grid.buses}

    counter = 0

    def add_candidate(
        recommendation_id: str,
        name: str,
        description: str,
        modifications: list[MitigationModification],
        target: str,
    ) -> None:
        nonlocal counter
        counter += 1
        candidates.append(
            MitigationCandidate(
                id=f"mitigation_{counter:03d}",
                recommendation_id=recommendation_id,
                name=name,
                description=description,
                modifications=modifications,
                expected_target=target,
            )
        )

    over_issues = [
        issue
        for issue in record.stress.issues
        if issue.category == IssueCategory.VOLTAGE_STRESS
        and issue.title == "Bus overvoltage"
        and issue.affected_component_id
    ]
    for issue in over_issues:
        bus = bus_by_id.get(issue.affected_component_id or "")
        if bus is None:
            continue
        candidate = None
        target_generator = None
        for generator in record.grid.generators:
            if generator.bus_id == bus.id and generator.type != GeneratorType.STORAGE:
                target_generator = generator
                break
        if target_generator is None:
            for generator in record.grid.generators:
                if generator.bus_id == bus.id:
                    target_generator = generator
                    break
        if target_generator is not None:
            candidate = MitigationCandidate(
                id=f"mitigation_{len(candidates) + 1:03d}",
                recommendation_id=next(
                    (rec.id for rec in record.recommendations if rec.category == "voltage"),
                    "",
                ),
                name=f"Reduce voltage support at {bus.name or bus.id}",
                description=(
                    f"Lower the reactive-power output of {target_generator.id} to reduce "
                    f"voltage at bus {bus.name or bus.id}."
                ),
                modifications=[
                    MitigationModification(
                        type="GENERATOR_SHUNT_REACTIVE",
                        new_value=max(target_generator.reactive_power_min, 0.0),
                        generator_id=target_generator.id,
                    )
                ],
                expected_target="Bus overvoltage",
            )
        if candidate is None:
            loads = [
                load for load in record.grid.loads if load.bus_id == bus.id
            ] or list(record.grid.loads)
            load = max(loads, key=lambda item: item.active_power)
            candidate = MitigationCandidate(
                id=f"mitigation_{len(candidates) + 1:03d}",
                recommendation_id="",
                name=f"Reduce load at {bus.name or bus.id}",
                description=(
                    f"Curtail load {load.id} to reduce voltage at bus {bus.name or bus.id}."
                ),
                modifications=[
                    MitigationModification(
                        type="LOAD_CURTAILMENT",
                        new_value=load.active_power * 0.5,
                        load_id=load.id,
                    )
                ],
                expected_target="Bus overvoltage",
            )
        add_candidate(
            candidate.recommendation_id,
            candidate.name,
            candidate.description,
            candidate.modifications,
            candidate.expected_target,
        )

    overloaded_issues = [
        issue
        for issue in record.stress.issues
        if issue.category == IssueCategory.TRANSMISSION_STRESS
        and issue.title == "Transmission line overloaded"
        and issue.affected_component_id
    ]
    for issue in overloaded_issues:
        line = next(
            (line for line in record.grid.lines if line.id == issue.affected_component_id),
            None,
        )
        if line is None:
            continue
        loads_at_to_bus = [load for load in record.grid.loads if load.bus_id == line.to_bus]
        if loads_at_to_bus:
            load = max(loads_at_to_bus, key=lambda item: item.active_power)
            add_candidate(
                next(
                    (rec.id for rec in record.recommendations if rec.category == "transmission"),
                    "",
                ),
                f"Curtail load feeding {line.name or line.id}",
                (
                    f"Curtail load {load.id} at bus {line.to_bus} to reduce flow on line "
                    f"{line.name or line.id}."
                ),
                [
                    MitigationModification(
                        type="LOAD_CURTAILMENT",
                        new_value=load.active_power * 0.5,
                        load_id=load.id,
                    )
                ],
                "Transmission line overload",
            )

    return candidates


def run_mitigation_test(
    record: AnalysisRecord,
    candidate: MitigationCandidate,
    settings: Settings = default_settings,
) -> MitigationTestResult:
    base_stress = record.stress
    before_score = base_stress.score.overall_score if base_stress else 0.0
    before_classification = (
        base_stress.score.classification.value if base_stress else ""
    )

    modified_grid = record.grid.model_copy(deep=True)
    for modification in candidate.modifications:
        modified_grid = _apply_modification(modified_grid, modification)

    result = power_flow_service.run_power_flow(
        modified_grid,
        settings=settings,
    )
    if not result.converged:
        return MitigationTestResult(
            id=f"test_{candidate.id}",
            analysis_id=record.id,
            mitigation_id=candidate.id,
            mitigation_name=candidate.name,
            converged=False,
            before_score=before_score,
            before_classification=before_classification,
            notes="Power flow did not converge under this mitigation.",
        )

    after_stress = build_stress_analysis(
        analysis_id=record.id,
        grid_id=record.grid_id,
        grid=modified_grid,
        result=result,
        baseline=base_stress,
    )
    after_score = after_stress.score.overall_score

    before_fingerprint = {
        (issue.title, issue.affected_component_id)
        for issue in (base_stress.issues if base_stress else [])
    }
    after_fingerprint = {
        (issue.title, issue.affected_component_id) for issue in after_stress.issues
    }
    resolved_issues = [
        issue
        for issue in (base_stress.issues if base_stress else [])
        if (issue.title, issue.affected_component_id) not in after_fingerprint
    ]
    remaining_issues = [
        issue
        for issue in after_stress.issues
        if (issue.title, issue.affected_component_id) in before_fingerprint
    ]
    new_issues = [
        issue
        for issue in after_stress.issues
        if (issue.title, issue.affected_component_id) not in before_fingerprint
    ]

    metric_changes = [
        MetricChange(
            metric="Stress score",
            before=before_score,
            after=after_score,
            improvement=after_score < before_score,
        )
    ]
    if base_stress is not None and result.summary is not None:
        before_summary = _record_summary(record)
        if before_summary is not None:
            metric_changes.append(
                MetricChange(
                    metric="Total losses (MW)",
                    before=before_summary.total_losses_mw,
                    after=result.summary.total_losses_mw,
                    unit="MW",
                    improvement=result.summary.total_losses_mw
                    < before_summary.total_losses_mw,
                )
            )
            metric_changes.append(
                MetricChange(
                    metric="Min voltage (pu)",
                    before=before_summary.minimum_voltage_pu,
                    after=result.summary.minimum_voltage_pu,
                    improvement=result.summary.minimum_voltage_pu
                    >= before_summary.minimum_voltage_pu,
                )
            )
            metric_changes.append(
                MetricChange(
                    metric="Max loading (%)",
                    before=before_summary.maximum_line_loading,
                    after=result.summary.maximum_line_loading,
                    unit="%",
                    improvement=result.summary.maximum_line_loading
                    <= before_summary.maximum_line_loading,
                )
            )

    return MitigationTestResult(
        id=f"test_{candidate.id}",
        analysis_id=record.id,
        mitigation_id=candidate.id,
        mitigation_name=candidate.name,
        converged=True,
        before_score=before_score,
        before_classification=before_classification,
        after_score=after_score,
        after_classification=after_stress.score.classification.value,
        resolved_issues=resolved_issues,
        remaining_issues=remaining_issues,
        new_issues=new_issues,
        metric_changes=metric_changes,
        notes=(
            "Mitigation improved the stress score."
            if after_score < before_score
            else "Mitigation did not improve the stress score."
        ),
    )


def run_mitigation_tests(
    record: AnalysisRecord,
    settings: Settings = default_settings,
) -> list[MitigationTestResult]:
    return [
        run_mitigation_test(record, candidate, settings)
        for candidate in record.mitigation_candidates
    ]


def _record_summary(record: AnalysisRecord) -> PowerFlowSummary | None:
    return record.result.summary
