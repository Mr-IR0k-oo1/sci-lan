import { vi } from 'vitest';
import { API_BASE } from '../src/api/client';
import type {
  AnalysisRecord,
  ApiErrorDetail,
  GridModel,
  PowerFlowResult,
  StressAnalysisResult,
} from '../src/types';

export const sampleGrid: GridModel = {
  grid_id: 'sample',
  name: '5-bus sample',
  base_mva: 100,
  buses: [
    { id: 'B1', name: 'Slack', type: 'SLACK', base_voltage: 138, voltage_magnitude: 1.06, voltage_angle: 0 },
    { id: 'B2', name: 'PV1', type: 'PV', base_voltage: 138, voltage_magnitude: 1.04, voltage_angle: 0.66 },
    { id: 'B3', name: 'PV2', type: 'PV', base_voltage: 138, voltage_magnitude: 1.02, voltage_angle: 0.94 },
    { id: 'B4', name: 'Load A', type: 'PQ', base_voltage: 138, voltage_magnitude: 1.0, voltage_angle: -2.34 },
    { id: 'B5', name: 'Load B', type: 'PQ', base_voltage: 138, voltage_magnitude: 1.0, voltage_angle: -2.3 },
  ],
  lines: [
    { id: 'L1', name: 'L1', from_bus: 'B1', to_bus: 'B2', resistance: 0.02, reactance: 0.06, susceptance: 0.03, thermal_limit: 100 },
    { id: 'L2', name: 'L2', from_bus: 'B1', to_bus: 'B4', resistance: 0.08, reactance: 0.24, susceptance: 0.025, thermal_limit: 100 },
    { id: 'L3', name: 'L3', from_bus: 'B2', to_bus: 'B3', resistance: 0.06, reactance: 0.18, susceptance: 0.02, thermal_limit: 100 },
    { id: 'L4', name: 'L4', from_bus: 'B2', to_bus: 'B5', resistance: 0.06, reactance: 0.18, susceptance: 0.02, thermal_limit: 100 },
    { id: 'L5', name: 'L5', from_bus: 'B3', to_bus: 'B4', resistance: 0.04, reactance: 0.12, susceptance: 0.015, thermal_limit: 100 },
    { id: 'L6', name: 'L6', from_bus: 'B4', to_bus: 'B5', resistance: 0.01, reactance: 0.03, susceptance: 0.01, thermal_limit: 100 },
    { id: 'L7', name: 'L7', from_bus: 'B1', to_bus: 'B3', resistance: 0.04, reactance: 0.12, susceptance: 0.015, thermal_limit: 100 },
  ],
  generators: [
    { id: 'G1', name: 'Slack Gen', bus_id: 'B1', type: 'CONVENTIONAL', active_power: 17.5, reactive_power: 66, active_power_min: 0, active_power_max: 300, reactive_power_min: -100, reactive_power_max: 100, capacity_mwh: 0 },
    { id: 'G2', name: 'PV Gen 1', bus_id: 'B2', type: 'CONVENTIONAL', active_power: 40, reactive_power: 20, active_power_min: 0, active_power_max: 200, reactive_power_min: -60, reactive_power_max: 60, capacity_mwh: 0 },
    { id: 'G3', name: 'PV Gen 2', bus_id: 'B3', type: 'CONVENTIONAL', active_power: 60, reactive_power: -20, active_power_min: 0, active_power_max: 200, reactive_power_min: -60, reactive_power_max: 60, capacity_mwh: 0 },
  ],
  loads: [
    { id: 'D1', name: 'Load A', bus_id: 'B4', active_power: 65, reactive_power: 30 },
    { id: 'D2', name: 'Load B', bus_id: 'B5', active_power: 50, reactive_power: 25 },
  ],
};

export const scenarioGrid: GridModel = {
  ...sampleGrid,
  buses: sampleGrid.buses.map((bus) => (bus.id === 'B4' ? { ...bus, type: 'PQ' } : bus)),
  loads: sampleGrid.loads.map((load) =>
    load.id === 'D1' ? { ...load, active_power: 85, reactive_power: 40 } : load,
  ),
};

export const sampleResult: PowerFlowResult = {
  grid_id: 'sample',
  engine: 'python',
  status: 'success',
  converged: true,
  iterations: 4,
  max_mismatch: 1e-11,
  execution_time_ms: 1.5,
  buses: [
    { bus_id: 'B1', voltage_magnitude: 1.06, voltage_angle: 0, active_power: 17.5, reactive_power: 66, status: 'WARNING' },
    { bus_id: 'B2', voltage_magnitude: 1.04, voltage_angle: 0.66, active_power: 60, reactive_power: 7.8, status: 'NORMAL' },
    { bus_id: 'B3', voltage_magnitude: 1.02, voltage_angle: 0.94, active_power: 40, reactive_power: -24.6, status: 'NORMAL' },
    { bus_id: 'B4', voltage_magnitude: 0.997, voltage_angle: -2.34, active_power: -65, reactive_power: -30, status: 'NORMAL' },
    { bus_id: 'B5', voltage_magnitude: 0.996, voltage_angle: -2.3, active_power: -50, reactive_power: -25, status: 'NORMAL' },
  ],
  lines: [
    { line_id: 'L1', from_bus: 'B1', to_bus: 'B2', active_power_from: -8.7, reactive_power_from: 27.6, active_power_to: 8.9, reactive_power_to: -29.2, loading_percentage: 11.6, status: 'NORMAL' },
    { line_id: 'L2', from_bus: 'B1', to_bus: 'B4', active_power_from: 28.2, reactive_power_from: 25.4, active_power_to: -27.5, reactive_power_to: -24.9, loading_percentage: 19.0, status: 'NORMAL' },
    { line_id: 'L3', from_bus: 'B2', to_bus: 'B3', active_power_from: 12.3, reactive_power_from: 3.0, active_power_to: -12.1, reactive_power_to: -2.8, loading_percentage: 8.0, status: 'NORMAL' },
    { line_id: 'L4', from_bus: 'B2', to_bus: 'B5', active_power_from: 38.0, reactive_power_from: 11.0, active_power_to: -37.4, reactive_power_to: -10.4, loading_percentage: 22.0, status: 'NORMAL' },
    { line_id: 'L5', from_bus: 'B3', to_bus: 'B4', active_power_from: 28.0, reactive_power_from: -21.0, active_power_to: -27.4, reactive_power_to: 21.6, loading_percentage: 21.5, status: 'NORMAL' },
    { line_id: 'L6', from_bus: 'B4', to_bus: 'B5', active_power_from: 5.4, reactive_power_from: 13.6, active_power_to: -5.4, reactive_power_to: -13.3, loading_percentage: 14.0, status: 'NORMAL' },
    { line_id: 'L7', from_bus: 'B1', to_bus: 'B3', active_power_from: -2.6, reactive_power_from: 13.1, active_power_to: 2.6, reactive_power_to: -12.9, loading_percentage: 11.0, status: 'NORMAL' },
  ],
  summary: {
    total_generation_mw: 117.5,
    renewable_generation_mw: 0,
    total_load_mw: 115,
    total_losses_mw: 2.5,
    minimum_voltage_pu: 0.996,
    maximum_voltage_pu: 1.06,
    maximum_line_loading: 22.0,
    overloaded_lines: 0,
  },
  impact_score: { score: 96.7, grade: 'A', categories: {}, message: 'Grid is healthy.' },
};

export const scenarioResult: PowerFlowResult = {
  ...sampleResult,
  summary: {
    ...sampleResult.summary!,
    total_generation_mw: 137.5,
    total_load_mw: 135,
    total_losses_mw: 2.5,
    maximum_voltage_pu: 1.06,
  },
  impact_score: { score: 94.2, grade: 'A', categories: {}, message: 'Grid is healthy.' },
};

export const whatIfResult: PowerFlowResult = {
  ...sampleResult,
  summary: {
    ...sampleResult.summary!,
    total_generation_mw: 137.5,
    renewable_generation_mw: 100,
    total_losses_mw: 3.1,
  },
  impact_score: { score: 97.2, grade: 'A', categories: {}, message: 'Grid is healthy.' },
};

type MockHandler = (init?: RequestInit) => { status: number; body?: unknown };

export function installFetchMock(routes: Record<string, MockHandler>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = String(input);
    const path = raw.replace(API_BASE, '');
    const method = (init?.method ?? 'GET').toUpperCase();
    const key = `${method} ${path}`;
    const handler = routes[key];
    if (!handler) {
      const detail: ApiErrorDetail = { code: 'not_found', message: `No mock for ${key}` };
      return new Response(JSON.stringify({ detail }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    const result = handler(init);
    return new Response(result.body === undefined ? null : JSON.stringify(result.body), {
      status: result.status,
      headers: { 'Content-Type': 'application/json' },
    });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

export function baseRoutes() {
  return {
    'GET /grids': () => ({ status: 200, body: [sampleGrid] }),
    'GET /grids/sample': () => ({ status: 200, body: sampleGrid }),
    'POST /grids/sample/validate': () => ({ status: 200, body: { valid: true, errors: [] } }),
    'GET /grids/sample/scenarios': () => ({ status: 200, body: [] }),
  };
}

export const healthyStress: StressAnalysisResult = {
  analysis_id: 'analysis-1',
  grid_id: 'sample',
  score: {
    overall_score: 8.0,
    classification: 'LOW',
    components: [
      { key: 'voltage', label: 'Voltage', score: 0, reason: 'All bus voltages within limits.' },
      { key: 'transmission', label: 'Transmission', score: 0, reason: 'All lines within limits.' },
      { key: 'generation', label: 'Generation', score: 0, reason: 'Generation balanced.' },
      { key: 'renewable', label: 'Renewable Impact', score: 80, reason: 'No renewables.' },
    ],
    reasons: ['Stress score is LOW (8/100) from 0 contributing component(s).'],
  },
  buses: [
    { bus_id: 'B1', bus_name: 'Slack', voltage_pu: 1.06, classification: 'NORMAL', severity: 'NORMAL', deviation_from_nominal: 0.06, deviation_from_limit: 0 },
    { bus_id: 'B2', bus_name: 'PV1', voltage_pu: 1.04, classification: 'NORMAL', severity: 'NORMAL', deviation_from_nominal: 0.04, deviation_from_limit: 0 },
  ],
  lines: [
    { line_id: 'L1', line_name: 'L1', from_bus: 'B1', to_bus: 'B2', loading_percentage: 30, thermal_limit: 100, status: 'NORMAL', severity: 'NORMAL', margin_remaining: 70 },
  ],
  generation: {
    total_generation_mw: 117.5,
    total_load_mw: 115,
    total_losses_mw: 2.5,
    slack_generation_mw: 17.5,
    slack_max_mw: 300,
    available_reserve_mw: 282.5,
    renewable_generation_mw: 0,
    detections: [],
    generators_at_limit: [],
    status: 'BALANCED',
    severity: 'NORMAL',
  },
  renewable: {
    renewable_penetration: 0,
    renewable_generation_mw: 0,
    impact_level: 'NEUTRAL',
    new_violations: [],
    resolved_violations: [],
    reason: 'No renewable generation present in this analysis.',
  },
  issues: [],
};

export const stressedAnalysis: AnalysisRecord = {
  id: 'analysis-2',
  grid_id: 'sample',
  scenario_id: null,
  engine: 'python',
  timestamp: '2026-01-01T00:00:00Z',
  grid: sampleGrid,
  result: sampleResult,
  stress: {
    ...healthyStress,
    analysis_id: 'analysis-2',
    score: {
      overall_score: 62.5,
      classification: 'MODERATE',
      components: [
        { key: 'voltage', label: 'Voltage', score: 55, reason: 'Worst voltage stress at Bus B4.' },
        { key: 'transmission', label: 'Transmission', score: 80, reason: 'Line L1 overloaded.' },
        { key: 'generation', label: 'Generation', score: 20, reason: 'Slack near limit.' },
        { key: 'renewable', label: 'Renewable Impact', score: 60, reason: 'High renewable penetration.' },
      ],
      reasons: [
        'Stress score is MODERATE (62.5/100) from 3 contributing component(s).',
        'Line L1 overloaded.',
      ],
    },
    buses: [
      { bus_id: 'B4', bus_name: 'Load A', voltage_pu: 0.88, classification: 'UNDER_VOLTAGE', severity: 'CRITICAL', deviation_from_nominal: 0.12, deviation_from_limit: 0.07 },
      { bus_id: 'B5', bus_name: 'Load B', voltage_pu: 0.99, classification: 'NORMAL', severity: 'NORMAL', deviation_from_nominal: 0.01, deviation_from_limit: 0 },
    ],
    lines: [
      { line_id: 'L1', line_name: 'L1', from_bus: 'B1', to_bus: 'B2', loading_percentage: 118, thermal_limit: 60, status: 'OVERLOADED', severity: 'CRITICAL', margin_remaining: -18 },
    ],
    generation: {
      total_generation_mw: 260,
      total_load_mw: 270,
      total_losses_mw: 10,
      slack_generation_mw: 300,
      slack_max_mw: 300,
      available_reserve_mw: 0,
      renewable_generation_mw: 120,
      detections: ['GENERATION_INSUFFICIENT', 'GENERATOR_AT_LIMIT'],
      generators_at_limit: ['G1'],
      status: 'AT_LIMIT',
      severity: 'CRITICAL',
    },
    renewable: {
      renewable_penetration: 44.4,
      renewable_generation_mw: 120,
      impact_level: 'HIGH_RISK',
      new_violations: ['VOLTAGE_STRESS:BUS:B4'],
      resolved_violations: [],
      reason: 'Renewable scenario introduced 1 new violation(s) without resolving any.',
    },
    issues: [
      {
        id: 'issue_001',
        category: 'VOLTAGE_STRESS',
        severity: 'CRITICAL',
        affected_component_type: 'BUS',
        affected_component_id: 'B4',
        title: 'Bus undervoltage',
        description: 'Bus voltage 0.880 pu is below the configured lower limit.',
        evidence: { voltage_pu: 0.88, normal_low: 0.95 },
        detected_from: 'power_flow',
      },
      {
        id: 'issue_002',
        category: 'TRANSMISSION_STRESS',
        severity: 'CRITICAL',
        affected_component_type: 'LINE',
        affected_component_id: 'L1',
        title: 'Transmission line overloaded',
        description: 'Line loading exceeds its configured thermal limit.',
        evidence: { loading_percentage: 118 },
        detected_from: 'power_flow',
      },
      {
        id: 'issue_003',
        category: 'GENERATION_BALANCE',
        severity: 'CRITICAL',
        affected_component_type: 'SYSTEM',
        affected_component_id: null,
        title: 'Generation may be insufficient',
        description: 'Available generation is at or near its maximum capacity.',
        evidence: { slack_generation_mw: 300 },
        detected_from: 'power_flow',
      },
    ],
  },
  recommendations: [
    {
      id: 'rec_001',
      title: 'Add shunt compensation to support voltage',
      category: 'voltage',
      priority: 'HIGH',
      description: 'Add shunt capacitors or adjust transformer taps to raise voltage at buses: B4.',
      reason: 'Add shunt capacitors or adjust transformer taps to raise voltage at buses: B4.',
      related_issue_ids: ['issue_001'],
      suggested_actions: ['Install shunt capacitor banks at the affected buses.'],
      expected_effect: ['Raise the affected bus voltages back into the normal band.'],
      confidence: 'HIGH',
    },
    {
      id: 'rec_002',
      title: 'Reduce load on overloaded transmission lines',
      category: 'transmission',
      priority: 'HIGH',
      description: 'Dispatch generation or curtail load to reduce flow on overloaded lines: L1.',
      reason: 'Dispatch generation or curtail load to reduce flow on overloaded lines: L1.',
      related_issue_ids: ['issue_002'],
      suggested_actions: ['Curtail the most sensitive loads.'],
      expected_effect: ['Bring line loading below the configured thermal limit.'],
      confidence: 'HIGH',
    },
    {
      id: 'rec_003',
      title: 'Add storage or stability controls for renewable integration',
      category: 'renewable',
      priority: 'MEDIUM',
      description: 'Renewable integration introduces or worsens violations.',
      reason: 'Renewable integration introduces or worsens violations.',
      related_issue_ids: [],
      suggested_actions: ['Add battery storage.'],
      expected_effect: ['Neutralize new violations.'],
      confidence: 'MEDIUM',
    },
  ],
  mitigation_candidates: [
    {
      id: 'mitigation_001',
      recommendation_id: 'rec_002',
      name: 'Curtail load feeding Line 1-2',
      description: 'Curtail load D1 to reduce flow on line L1.',
      modifications: [{ type: 'LOAD_CURTAILMENT', new_value: 32.5, generator_id: null, load_id: 'D1' }],
      expected_target: 'Transmission line overload',
    },
  ],
  mitigation_tests: [],
};

export const mitigationTestResult = {
  id: 'test_mitigation_001',
  analysis_id: 'analysis-2',
  mitigation_id: 'mitigation_001',
  mitigation_name: 'Curtail load feeding Line 1-2',
  converged: true,
  before_score: 62.5,
  before_classification: 'MODERATE',
  after_score: 38.2,
  after_classification: 'LOW',
  resolved_issues: [
    {
      id: 'issue_002',
      category: 'TRANSMISSION_STRESS',
      severity: 'CRITICAL',
      affected_component_type: 'LINE',
      affected_component_id: 'L1',
      title: 'Transmission line overloaded',
      description: 'Line loading exceeds its configured thermal limit.',
      evidence: {},
      detected_from: 'power_flow',
    },
  ],
  remaining_issues: [],
  new_issues: [],
  metric_changes: [
    { metric: 'Stress score', before: 62.5, after: 38.2, unit: '', improvement: true },
  ],
  notes: 'Mitigation improved the stress score.',
};
