from typing import Any

from pydantic import BaseModel, Field

from app.domain.models import GridModel


class PowerFlowRequest(BaseModel):
    engine: str | None = None
    tolerance: float | None = Field(default=None, gt=0)
    max_iterations: int | None = Field(default=None, gt=0)


class WhatIfRequest(BaseModel):
    grid: GridModel | None = None
    solar_output_mw: float | None = Field(default=None, gt=0)
    wind_output_mw: float | None = Field(default=None, gt=0)
    battery_output_mw: float | None = None
    load_scale: float | None = Field(default=None, gt=0)
    engine: str | None = None
    tolerance: float | None = Field(default=None, gt=0)
    max_iterations: int | None = Field(default=None, gt=0)


class EngineInfoResponse(BaseModel):
    name: str
    available: bool
    version: str | None = None
    status: str


class EngineRegistryResponse(BaseModel):
    engines: list[EngineInfoResponse]
    default_engine: str


class EngineComparisonRequest(BaseModel):
    grid: GridModel
    tolerance: float | None = Field(default=None, gt=0)
    max_iterations: int | None = Field(default=None, gt=0)
    voltage_tolerance: float = Field(default=1e-4, gt=0)
    angle_tolerance_deg: float = Field(default=1e-3, gt=0)
    flow_tolerance_pu: float = Field(default=0.02, gt=0)


class EngineRunInfo(BaseModel):
    available: bool
    converged: bool | None = None
    engine_version: str | None = None
    execution_time_ms: float | None = None
    error: str | None = None


class EngineComparisonResponse(BaseModel):
    python: EngineRunInfo | None = None
    scilab: EngineRunInfo
    comparison: dict[str, Any] | None = None


class ScilabStatusResponse(BaseModel):
    available: bool
    version: str | None = None
    executable_path: str | None = None
    health_check: str
    supported_operations: list[str]
    last_checked: str | None = None
    message: str = ""


class AnalysisRun(BaseModel):
    id: str
    timestamp: str
    grid_id: str
    scenario_id: str | None = None
    case_study_id: str | None = None
    engine: str
    engine_version: str | None = None
    input_hash: str
    status: str
    execution_time_ms: float
    converged: bool
    stress_score: float | None = None
    issue_count: int = 0
