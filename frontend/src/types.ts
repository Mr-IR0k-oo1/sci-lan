export type BusType = 'SLACK' | 'PV' | 'PQ';
export type GeneratorType = 'CONVENTIONAL' | 'SOLAR' | 'WIND' | 'STORAGE';
export type BusStatus = 'NORMAL' | 'WARNING' | 'CRITICAL';
export type LineStatus = 'NORMAL' | 'WARNING' | 'OVERLOADED';

export interface Bus {
  id: string;
  name: string;
  type: BusType;
  base_voltage: number;
  voltage_magnitude: number;
  voltage_angle: number;
}

export interface TransmissionLine {
  id: string;
  name: string;
  from_bus: string;
  to_bus: string;
  resistance: number;
  reactance: number;
  susceptance: number;
  thermal_limit: number;
}

export interface Generator {
  id: string;
  name: string;
  bus_id: string;
  type: GeneratorType;
  active_power: number;
  reactive_power: number;
  active_power_min: number;
  active_power_max: number;
  reactive_power_min: number;
  reactive_power_max: number;
  capacity_mwh: number;
}

export interface Load {
  id: string;
  name: string;
  bus_id: string;
  active_power: number;
  reactive_power: number;
}

export interface GridModel {
  grid_id: string;
  name: string;
  base_mva: number;
  buses: Bus[];
  lines: TransmissionLine[];
  generators: Generator[];
  loads: Load[];
}

export interface ValidationIssue {
  code: string;
  message: string;
  location: string;
}

export interface ValidationResponse {
  valid: boolean;
  errors: ValidationIssue[];
}

export interface BusResult {
  bus_id: string;
  voltage_magnitude: number;
  voltage_angle: number;
  active_power: number;
  reactive_power: number;
  status: BusStatus;
}

export interface LineResult {
  line_id: string;
  from_bus: string;
  to_bus: string;
  active_power_from: number;
  reactive_power_from: number;
  active_power_to: number;
  reactive_power_to: number;
  loading_percentage: number;
  status: LineStatus;
}

export interface PowerFlowSummary {
  total_generation_mw: number;
  renewable_generation_mw: number;
  total_load_mw: number;
  total_losses_mw: number;
  minimum_voltage_pu: number;
  maximum_voltage_pu: number;
  maximum_line_loading: number;
  overloaded_lines: number;
}

export interface ImpactCategory {
  score: number;
  detail: string;
}

export interface GridImpactScore {
  score: number;
  grade: string;
  categories: Record<string, ImpactCategory>;
  message: string;
}

export interface PowerFlowResult {
  grid_id: string;
  analysis_id: string;
  input_hash: string;
  engine: string;
  status: string;
  converged: boolean;
  iterations: number;
  max_mismatch: number;
  execution_time_ms: number;
  buses: BusResult[];
  lines: LineResult[];
  summary: PowerFlowSummary | null;
  impact_score: GridImpactScore | null;
}

export interface Scenario {
  id: string;
  name: string;
  grid: GridModel;
}

export interface ScenarioSummary {
  id: string;
  name: string;
}

export interface EngineInfo {
  name: string;
  available: boolean;
  version: string | null;
  status: string;
}

export interface EngineRegistry {
  engines: EngineInfo[];
  default_engine: string;
}

export interface ScilabStatus {
  available: boolean;
  version: string | null;
  executable_path: string | null;
  health_check: string;
  supported_operations: string[];
  last_checked: string | null;
  message: string;
}

export interface EngineRunInfo {
  available: boolean;
  converged: boolean | null;
  engine_version: string | null;
  execution_time_ms: number | null;
  error: string | null;
}

export interface EngineComparison {
  voltage_difference_max: number;
  angle_difference_max: number;
  line_flow_difference_max: number;
  within_tolerance: boolean;
}

export interface EngineComparisonResponse {
  python: EngineRunInfo | null;
  scilab: EngineRunInfo;
  comparison: EngineComparison | null;
}

export interface PowerFlowRequest {
  engine?: string;
  tolerance?: number;
  max_iterations?: number;
}

export interface CompareEnginesRequest {
  grid: GridModel;
  tolerance?: number;
  max_iterations?: number;
  voltage_tolerance?: number;
  angle_tolerance_deg?: number;
  flow_tolerance_pu?: number;
}

export interface WhatIfRequest {
  grid?: GridModel;
  solar_output_mw?: number;
  wind_output_mw?: number;
  battery_output_mw?: number;
  load_scale?: number;
  engine?: string;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: ValidationIssue[];
  max_mismatch?: number;
  iterations?: number;
}

export type ComponentKind = 'bus' | 'line' | 'generator' | 'load';

export interface ComponentSelection {
  kind: ComponentKind;
  id: string;
}

// --- Stress analysis / recommendations --------------------------------------

export type SeverityLevel = 'NORMAL' | 'WARNING' | 'CRITICAL';
export type StressLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
export type VoltageClass = 'NORMAL' | 'UNDER_VOLTAGE' | 'OVER_VOLTAGE';
export type IssueCategory =
  | 'VOLTAGE_STRESS'
  | 'TRANSMISSION_STRESS'
  | 'GENERATION_BALANCE'
  | 'RENEWABLE_IMPACT';
export type ImpactLevel = 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE' | 'HIGH_RISK';
export type GenerationDetection =
  | 'GENERATION_INSUFFICIENT'
  | 'GENERATOR_AT_LIMIT'
  | 'EXCESS_GENERATION'
  | 'IMBALANCED_SYSTEM';
export type RecommendationPriority = 'LOW' | 'MEDIUM' | 'HIGH';
export type ConfidenceLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface BusStress {
  bus_id: string;
  bus_name: string;
  voltage_pu: number;
  classification: VoltageClass;
  severity: SeverityLevel;
  deviation_from_nominal: number;
  deviation_from_limit: number;
}

export interface LineStress {
  line_id: string;
  line_name: string;
  from_bus: string;
  to_bus: string;
  loading_percentage: number;
  thermal_limit: number;
  status: LineStatus;
  severity: SeverityLevel;
  margin_remaining: number;
}

export interface GenerationBalance {
  total_generation_mw: number;
  total_load_mw: number;
  total_losses_mw: number;
  slack_generation_mw: number;
  slack_max_mw: number;
  available_reserve_mw: number;
  renewable_generation_mw: number;
  detections: GenerationDetection[];
  generators_at_limit: string[];
  status: string;
  severity: SeverityLevel;
}

export interface RenewableImpact {
  renewable_penetration: number;
  renewable_generation_mw: number;
  impact_level: ImpactLevel;
  new_violations: string[];
  resolved_violations: string[];
  reason: string;
}

export interface StressComponentScore {
  key: string;
  label: string;
  score: number;
  reason: string;
}

export interface StressScore {
  overall_score: number;
  classification: StressLevel;
  components: StressComponentScore[];
  reasons: string[];
}

export type EvidenceValue = number | string;

export interface StressIssue {
  id: string;
  category: IssueCategory;
  severity: SeverityLevel;
  affected_component_type: string;
  affected_component_id: string | null;
  title: string;
  description: string;
  evidence: Record<string, EvidenceValue>;
  detected_from: string;
}

export interface StressAnalysisResult {
  analysis_id: string;
  grid_id: string;
  score: StressScore;
  buses: BusStress[];
  lines: LineStress[];
  generation: GenerationBalance;
  renewable: RenewableImpact;
  issues: StressIssue[];
}

export interface Recommendation {
  id: string;
  title: string;
  category: string;
  priority: RecommendationPriority;
  description: string;
  reason: string;
  related_issue_ids: string[];
  suggested_actions: string[];
  expected_effect: string[];
  confidence: ConfidenceLevel;
}

export interface MitigationModification {
  type: string;
  new_value: number;
  generator_id: string | null;
  load_id: string | null;
}

export interface MitigationCandidate {
  id: string;
  recommendation_id: string;
  name: string;
  description: string;
  modifications: MitigationModification[];
  expected_target: string;
}

export interface MetricChange {
  metric: string;
  before: number;
  after: number;
  unit: string;
  improvement: boolean;
}

export interface MitigationTestResult {
  id: string;
  analysis_id: string;
  mitigation_id: string;
  mitigation_name: string;
  converged: boolean;
  before_score: number;
  before_classification: string;
  after_score: number;
  after_classification: string;
  resolved_issues: StressIssue[];
  remaining_issues: StressIssue[];
  new_issues: StressIssue[];
  metric_changes: MetricChange[];
  notes: string;
}

export interface AnalysisRecord {
  id: string;
  grid_id: string;
  scenario_id: string | null;
  engine: string;
  timestamp: string;
  grid: GridModel;
  result: PowerFlowResult;
  stress: StressAnalysisResult;
  recommendations: Recommendation[];
  mitigation_candidates: MitigationCandidate[];
  mitigation_tests: MitigationTestResult[];
}
