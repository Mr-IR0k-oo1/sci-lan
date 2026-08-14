"""Export analysis records as JSON or CSV.

Only public, analysis-level data is exported — the in-memory records contain no
hidden internal state, and the payloads are curated explicitly so nothing
accidental leaks out.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from app.domain.recommendation_models import AnalysisRecord


def _export_json(record: AnalysisRecord) -> dict:
    payload = {
        "metadata": {
            "id": record.id,
            "grid_id": record.grid_id,
            "scenario_id": record.scenario_id,
            "engine": record.engine,
            "engine_version": record.result.engine_version,
            "timestamp": record.timestamp,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        },
        "grid": {
            "id": record.grid.grid_id,
            "name": record.grid.name,
            "base_mva": record.grid.base_mva,
            "buses": [bus.model_dump() for bus in record.grid.buses],
            "lines": [line.model_dump() for line in record.grid.lines],
            "generators": [gen.model_dump() for gen in record.grid.generators],
            "loads": [load.model_dump() for load in record.grid.loads],
        },
        "result": {
            "converged": record.result.converged,
            "iterations": record.result.iterations,
            "max_mismatch": record.result.max_mismatch,
            "summary": record.result.summary.model_dump(),
            "buses": [bus.model_dump() for bus in record.result.buses],
            "lines": [line.model_dump() for line in record.result.lines],
        },
        "stress": record.stress.model_dump() if record.stress else None,
        "issues": record.stress.issues if record.stress else [],
        "recommendations": [rec.model_dump() for rec in record.recommendations],
        "mitigation_candidates": [c.model_dump() for c in record.mitigation_candidates],
        "mitigation_tests": [t.model_dump() for t in record.mitigation_tests],
    }
    return payload


def _export_csv(record: AnalysisRecord) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["SECTION", "metadata"])
    writer.writerow(["field", "value"])
    writer.writerow(["id", record.id])
    writer.writerow(["grid_id", record.grid_id])
    writer.writerow(["scenario_id", record.scenario_id or ""])
    writer.writerow(["engine", record.engine])
    writer.writerow(["engine_version", record.result.engine_version or ""])
    writer.writerow(["timestamp", record.timestamp])

    writer.writerow([])
    writer.writerow(["SECTION", "bus_results"])
    writer.writerow(
        [
            "bus_id",
            "voltage_magnitude",
            "voltage_angle_deg",
            "active_power_mw",
            "reactive_power_mvar",
            "status",
        ]
    )
    for bus in record.result.buses:
        writer.writerow(
            [
                bus.bus_id,
                bus.voltage_magnitude,
                bus.voltage_angle,
                bus.active_power,
                bus.reactive_power,
                bus.status.value if hasattr(bus.status, "value") else bus.status,
            ]
        )

    writer.writerow([])
    writer.writerow(["SECTION", "line_results"])
    writer.writerow(
        [
            "line_id",
            "from_bus",
            "to_bus",
            "active_power_from_mw",
            "reactive_power_from_mvar",
            "active_power_to_mw",
            "reactive_power_to_mvar",
            "loading_pct",
            "status",
        ]
    )
    for line in record.result.lines:
        writer.writerow(
            [
                line.line_id,
                line.from_bus,
                line.to_bus,
                line.active_power_from,
                line.reactive_power_from,
                line.active_power_to,
                line.reactive_power_to,
                line.loading_percentage,
                line.status.value if hasattr(line.status, "value") else line.status,
            ]
        )

    writer.writerow([])
    writer.writerow(["SECTION", "stress_issues"])
    writer.writerow(
        [
            "issue_id",
            "category",
            "severity",
            "title",
            "description",
            "affected_component_type",
            "affected_component_id",
        ]
    )
    if record.stress:
        for issue in record.stress.issues:
            writer.writerow(
                [
                    issue.id,
                    issue.category.value if hasattr(issue.category, "value") else issue.category,
                    issue.severity.value if hasattr(issue.severity, "value") else issue.severity,
                    issue.title,
                    issue.description,
                    issue.affected_component_type,
                    issue.affected_component_id or "",
                ]
            )

    writer.writerow([])
    writer.writerow(["SECTION", "recommendations"])
    writer.writerow(["id", "title", "category", "priority", "confidence", "related_issue_ids"])
    for rec in record.recommendations:
        writer.writerow(
            [
                rec.id,
                rec.title,
                rec.category,
                rec.priority.value,
                rec.confidence.value,
                "|".join(rec.related_issue_ids),
            ]
        )

    writer.writerow([])
    writer.writerow(["SECTION", "mitigation_tests"])
    writer.writerow(
        [
            "id",
            "mitigation_id",
            "mitigation_name",
            "converged",
            "before_score",
            "after_score",
            "resolved_issues",
            "remaining_issues",
            "new_issues",
        ]
    )
    for test in record.mitigation_tests:
        writer.writerow(
            [
                test.id,
                test.mitigation_id,
                test.mitigation_name,
                test.converged,
                test.before_score,
                test.after_score,
                len(test.resolved_issues),
                len(test.remaining_issues),
                len(test.new_issues),
            ]
        )

    return buffer.getvalue()


def _export_markdown(record: AnalysisRecord) -> str:
    lines = []
    lines.append("# GridFlex Analysis Report\n")
    
    lines.append("## Analysis Summary\n")
    lines.append(f"Grid: {record.grid.name}")
    lines.append(f"Engine: {record.engine}")
    lines.append(f"Status: {'Converged' if record.result.converged else 'Not Converged'}\n")
    
    lines.append("## Grid Health\n")
    if record.stress:
        lines.append(f"Stress Score: {record.stress.impact_score:.2f} / 100")
        lines.append(f"Classification: {record.stress.classification.value if hasattr(record.stress.classification, 'value') else record.stress.classification}\n")
    else:
        lines.append("No stress analysis available.\n")
        
    lines.append("## Detected Issues\n")
    if record.stress and record.stress.issues:
        for i, issue in enumerate(record.stress.issues, 1):
            lines.append(f"### Issue {i}")
            lines.append(f"{issue.title}")
            lines.append(f"Evidence: {issue.description}\n")
    else:
        lines.append("No issues detected.\n")
        
    lines.append("## Recommendations\n")
    for rec in record.recommendations:
        lines.append(f"### {rec.title}")
        lines.append(f"{rec.description}\n")
        
    lines.append("## Mitigation Tests\n")
    for test in record.mitigation_tests:
        lines.append(f"### {test.mitigation_name}")
        lines.append(f"Before: {test.before_score:.2f}")
        lines.append(f"After: {test.after_score:.2f}")
        lines.append(f"Status: {test.after_classification}\n")
        
    lines.append("---\n")
    lines.append("*Results are based on the modeled network and configured assumptions. GridFlex is a planning and decision-support tool and does not replace detailed protection, transient stability, equipment, or regulatory studies.*\n")
    
    return "\n".join(lines)


def export_analysis(
    record: AnalysisRecord,
    fmt: str = "json",
) -> tuple[str, str, dict | str]:
    """Return (filename, content_type, body) for the requested format."""
    if fmt == "json":
        body = _export_json(record)
        return f"{record.id}.json", "application/json", body
    if fmt == "csv":
        return f"{record.id}.csv", "text/csv", _export_csv(record)
    if fmt == "markdown":
        return f"{record.id}.md", "text/markdown", _export_markdown(record)
    raise ValueError(f"Unsupported export format '{fmt}'.")
