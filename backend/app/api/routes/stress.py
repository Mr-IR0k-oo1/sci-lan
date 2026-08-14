from typing import Literal

from fastapi import APIRouter, Response

from app.domain.recommendation_models import (
    AnalysisRecord,
    MitigationCandidate,
    MitigationTestResult,
)
from app.schemas.stress import (
    ComparativeAnalysisRequest,
    MitigationTestRequest,
    StressAnalysisRequest,
)
from app.services import (
    analysis_history_service,
    export_service,
    grid_service,
    stress_analysis_service,
)

router = APIRouter(tags=["stress"])


@router.post(
    "/grids/{grid_id}/stress",
    response_model=AnalysisRecord,
)
def run_stress_analysis(
    grid_id: str, request: StressAnalysisRequest
) -> AnalysisRecord:
    grid_service.get_grid(grid_id)
    return stress_analysis_service.run_full_analysis(
        grid_id,
        tolerance=request.tolerance,
        max_iterations=request.max_iterations,
        engine_name=request.engine,
    )


@router.post(
    "/stress/comparative",
    response_model=AnalysisRecord,
)
def run_comparative_analysis(
    request: ComparativeAnalysisRequest,
) -> AnalysisRecord:
    return stress_analysis_service.run_comparative_analysis(
        request.analysis_id,
        grid_id=request.grid_id,
        tolerance=request.tolerance,
        max_iterations=request.max_iterations,
        engine_name=request.engine,
    )


@router.get(
    "/analyses/{analysis_id}/stress",
    response_model=AnalysisRecord,
)
def get_stress_analysis(analysis_id: str) -> AnalysisRecord:
    return analysis_history_service.get_analysis(analysis_id)


@router.get(
    "/analyses/{analysis_id}/mitigation-candidates",
    response_model=list[MitigationCandidate],
)
def list_mitigation_candidates(analysis_id: str) -> list[MitigationCandidate]:
    record = analysis_history_service.get_analysis(analysis_id)
    return record.mitigation_candidates


@router.get(
    "/analyses/{analysis_id}/export",
    responses={
        200: {
            "content": {
                "application/json": {},
                "text/csv": {},
            }
        }
    },
)
def export_analysis(
    analysis_id: str,
    format: Literal["json", "csv"] = "json",
) -> Response:
    record = analysis_history_service.get_analysis(analysis_id)
    filename, content_type, body = export_service.export_analysis(record, format)
    if isinstance(body, dict):
        import json

        content = json.dumps(body, indent=2, default=str)
    else:
        content = body
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/analyses/{analysis_id}/mitigation-tests",
    response_model=list[MitigationTestResult],
)
def run_mitigation_tests(
    analysis_id: str, request: MitigationTestRequest
) -> list[MitigationTestResult]:
    record = analysis_history_service.get_analysis(analysis_id)
    if not record.mitigation_candidates:
        return []
    if request.run_all or request.mitigation_id is None:
        return stress_analysis_service.run_mitigation_tests(record)
    candidate = next(
        (
            candidate
            for candidate in record.mitigation_candidates
            if candidate.id == request.mitigation_id
        ),
        None,
    )
    if candidate is None:
        return []
    return [stress_analysis_service.run_mitigation_test(record, candidate)]
