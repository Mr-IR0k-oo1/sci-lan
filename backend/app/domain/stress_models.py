from pydantic import BaseModel, Field

from app.domain.enums import (
    BusStatus,
    GenerationDetection,
    ImpactLevel,
    IssueCategory,
    LineStatus,
    SeverityLevel,
    StressLevel,
    VoltageClass,
)

# Values inside evidence dicts may be numeric or short strings.
EvidenceValue = float | str | int


class BusStress(BaseModel):
    bus_id: str
    bus_name: str = ""
    voltage_pu: float
    classification: VoltageClass
    severity: SeverityLevel
    deviation_from_nominal: float
    deviation_from_limit: float


class LineStress(BaseModel):
    line_id: str
    line_name: str = ""
    from_bus: str
    to_bus: str
    loading_percentage: float
    thermal_limit: float
    status: LineStatus
    severity: SeverityLevel
    margin_remaining: float


class GenerationBalance(BaseModel):
    total_generation_mw: float
    total_load_mw: float
    total_losses_mw: float
    slack_generation_mw: float
    slack_max_mw: float
    available_reserve_mw: float
    renewable_generation_mw: float
    detections: list[GenerationDetection] = Field(default_factory=list)
    generators_at_limit: list[str] = Field(default_factory=list)
    status: str = "BALANCED"
    severity: SeverityLevel = SeverityLevel.NORMAL


class RenewableImpact(BaseModel):
    renewable_penetration: float
    renewable_generation_mw: float
    impact_level: ImpactLevel
    new_violations: list[str] = Field(default_factory=list)
    resolved_violations: list[str] = Field(default_factory=list)
    reason: str = ""


class StressComponentScore(BaseModel):
    key: str
    label: str
    score: float
    reason: str


class StressScore(BaseModel):
    overall_score: float
    classification: StressLevel
    components: list[StressComponentScore]
    reasons: list[str]


class StressIssue(BaseModel):
    id: str
    category: IssueCategory
    severity: SeverityLevel
    affected_component_type: str
    affected_component_id: str | None = None
    title: str
    description: str
    evidence: dict[str, EvidenceValue] = Field(default_factory=dict)
    detected_from: str = "power_flow"


class StressAnalysisResult(BaseModel):
    analysis_id: str
    grid_id: str
    score: StressScore
    buses: list[BusStress]
    lines: list[LineStress]
    generation: GenerationBalance
    renewable: RenewableImpact
    issues: list[StressIssue]
