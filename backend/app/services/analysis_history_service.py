import uuid
from datetime import datetime, timezone

from app.core.exceptions import AnalysisNotFound
from app.domain.models import GridModel
from app.domain.recommendation_models import AnalysisRecord
from app.power_system.results import PowerFlowResult

_records: dict[str, AnalysisRecord] = {}


def record_analysis(
    grid: GridModel,
    result: PowerFlowResult,
    scenario_id: str | None = None,
) -> AnalysisRecord:
    record = AnalysisRecord(
        id=uuid.uuid4().hex[:8],
        grid_id=grid.grid_id,
        scenario_id=scenario_id,
        engine=result.engine,
        timestamp=datetime.now(timezone.utc).isoformat(),
        grid=grid.model_copy(deep=True),
        result=result,
    )
    _records[record.id] = record
    return record


def get_analysis(analysis_id: str) -> AnalysisRecord:
    if analysis_id not in _records:
        raise AnalysisNotFound(analysis_id)
    return _records[analysis_id]


def list_analyses() -> list[AnalysisRecord]:
    return list(_records.values())


def clear_analyses() -> None:
    _records.clear()
