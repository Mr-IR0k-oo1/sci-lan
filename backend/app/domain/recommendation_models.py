from pydantic import BaseModel, Field

from app.domain.enums import ConfidenceLevel, RecommendationPriority
from app.domain.models import GridModel
from app.domain.stress_models import StressAnalysisResult, StressIssue
from app.power_system.results import PowerFlowResult


class Recommendation(BaseModel):
    id: str
    title: str
    category: str
    priority: RecommendationPriority
    description: str
    reason: str
    related_issue_ids: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    expected_effect: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class MitigationModification(BaseModel):
    type: str
    new_value: float
    generator_id: str | None = None
    load_id: str | None = None


class MitigationCandidate(BaseModel):
    id: str
    recommendation_id: str
    name: str
    description: str
    modifications: list[MitigationModification] = Field(default_factory=list)
    expected_target: str


class MetricChange(BaseModel):
    metric: str
    before: float
    after: float
    unit: str = ""
    improvement: bool = False


class MitigationTestResult(BaseModel):
    id: str
    analysis_id: str
    mitigation_id: str
    mitigation_name: str
    converged: bool
    before_score: float = 0.0
    before_classification: str = ""
    after_score: float = 0.0
    after_classification: str = ""
    resolved_issues: list[StressIssue] = Field(default_factory=list)
    remaining_issues: list[StressIssue] = Field(default_factory=list)
    new_issues: list[StressIssue] = Field(default_factory=list)
    metric_changes: list[MetricChange] = Field(default_factory=list)
    notes: str = ""


class AnalysisRecord(BaseModel):
    id: str
    grid_id: str
    scenario_id: str | None = None
    engine: str
    timestamp: str
    grid: GridModel
    result: PowerFlowResult
    stress: StressAnalysisResult | None = None
    recommendations: list[Recommendation] = Field(default_factory=list)
    mitigation_candidates: list[MitigationCandidate] = Field(default_factory=list)
    mitigation_tests: list[MitigationTestResult] = Field(default_factory=list)
