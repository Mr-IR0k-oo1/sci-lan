from pydantic import BaseModel

from app.domain.models import GridModel


class Scenario(BaseModel):
    id: str
    name: str
    grid: GridModel


class ScenarioCreateRequest(BaseModel):
    id: str = ""
    name: str
    grid: GridModel


class ScenarioSummary(BaseModel):
    id: str
    name: str
