import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.schemas.analysis import AnalysisRun
from app.power_system.results import PowerFlowResult
from pydantic import BaseModel

class AnalysisRecord(BaseModel):
    run: AnalysisRun
    result: PowerFlowResult

_runs: Dict[str, AnalysisRecord] = {}

def create_analysis_run(
    grid_id: str,
    scenario_id: Optional[str],
    case_study_id: Optional[str],
    engine: str,
    engine_version: Optional[str],
    input_hash: str,
    result: PowerFlowResult,
) -> AnalysisRun:
    run_id = str(uuid.uuid4())
    stress_score = result.impact_score.score if result.impact_score else None
    
    # Calculate issues count based on buses/lines status
    issue_count = 0
    if result.converged:
        from app.domain.enums import BusStatus, LineStatus
        issue_count += sum(1 for b in result.buses if b.status != BusStatus.NORMAL)
        issue_count += sum(1 for l in result.lines if l.status != LineStatus.NORMAL)

    run = AnalysisRun(
        id=run_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        grid_id=grid_id,
        scenario_id=scenario_id,
        case_study_id=case_study_id,
        engine=engine,
        engine_version=engine_version,
        input_hash=input_hash,
        status="success" if result.converged else "not_converged",
        execution_time_ms=result.execution_time_ms,
        converged=result.converged,
        stress_score=stress_score,
        issue_count=issue_count
    )
    
    _runs[run_id] = AnalysisRecord(run=run, result=result)
    return run

def get_analysis_record(run_id: str) -> Optional[AnalysisRecord]:
    return _runs.get(run_id)
