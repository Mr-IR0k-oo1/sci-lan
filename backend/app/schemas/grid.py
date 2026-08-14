from pydantic import BaseModel

from app.domain.models import GridModel


class ValidationIssue(BaseModel):
    code: str
    message: str
    location: str = ""


class ValidationResponse(BaseModel):
    valid: bool
    errors: list[ValidationIssue] = []


class GridCreateRequest(GridModel):
    pass


class GridResponse(GridModel):
    pass
