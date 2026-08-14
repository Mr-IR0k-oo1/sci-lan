from pydantic import BaseModel, Field


class PowerFlowRequest(BaseModel):
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
