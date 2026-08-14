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
