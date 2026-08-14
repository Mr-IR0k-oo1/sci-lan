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

export interface PowerFlowRequest {
  engine?: string;
  tolerance?: number;
  max_iterations?: number;
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
