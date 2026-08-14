from pydantic import BaseModel, Field


class StressAnalysisRequest(BaseModel):
    engine: str | None = None
    tolerance: float | None = Field(default=None, gt=0)
    max_iterations: int | None = Field(default=None, gt=0)


class ComparativeAnalysisRequest(BaseModel):
    analysis_id: str
    grid_id: str | None = None
    engine: str | None = None
    tolerance: float | None = Field(default=None, gt=0)
    max_iterations: int | None = Field(default=None, gt=0)


class MitigationTestRequest(BaseModel):
    mitigation_id: str | None = None
    run_all: bool = False
