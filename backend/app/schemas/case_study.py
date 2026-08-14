from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ExpectedConditions(BaseModel):
    converged: bool
    max_voltage_pu: Optional[float] = None
    min_voltage_pu: Optional[float] = None
    overloaded_lines: Optional[int] = None

class CaseStudyMetadata(BaseModel):
    id: str
    name: str
    description: str
    objective: str

class CaseStudyDetails(CaseStudyMetadata):
    grid_id: str
    scenario: Dict[str, Any]
    expected_conditions: ExpectedConditions
    readme: str

class CaseStudyRunStep(BaseModel):
    name: str
    status: str
    message: Optional[str] = None
    result: Optional[Any] = None

class CaseStudyRunResponse(BaseModel):
    case_id: str
    status: str
    steps: List[CaseStudyRunStep]
    analysis: Optional[Dict[str, Any]] = None
    issues: List[Any] = []
    recommendations: List[Any] = []
    mitigation_result: Optional[Dict[str, Any]] = None
