import type { LineResult, LineStatus, PowerFlowResult } from '../types';

export interface MetricRow {
  metric: string;
  base: number;
  scenario: number;
  change: number;
  changePercent: number | null;
  unit: string;
}

export interface VoltageRow {
  busId: string;
  base: number;
  scenario: number;
  change: number;
  classification: 'improved' | 'warning' | 'violation' | 'unchanged';
}

export interface LineRow {
  lineId: string;
  baseLoading: number;
  scenarioLoading: number;
  baseStatus: LineStatus;
  scenarioStatus: LineStatus;
  transition: boolean;
}

interface MetricSpec {
  metric: string;
  unit: string;
  base: number;
  scenario: number;
}

export function buildMetricComparison(
  base: PowerFlowResult,
  scenario: PowerFlowResult,
): MetricRow[] {
  const baseSummary = base.summary;
  const scenarioSummary = scenario.summary;
  if (!baseSummary || !scenarioSummary) return [];

  const specs: MetricSpec[] = [
    { metric: 'Total generation', unit: 'MW', base: baseSummary.total_generation_mw, scenario: scenarioSummary.total_generation_mw },
    { metric: 'Renewable generation', unit: 'MW', base: baseSummary.renewable_generation_mw, scenario: scenarioSummary.renewable_generation_mw },
    { metric: 'Total load', unit: 'MW', base: baseSummary.total_load_mw, scenario: scenarioSummary.total_load_mw },
    { metric: 'Total losses', unit: 'MW', base: baseSummary.total_losses_mw, scenario: scenarioSummary.total_losses_mw },
    { metric: 'Max voltage', unit: 'pu', base: baseSummary.maximum_voltage_pu, scenario: scenarioSummary.maximum_voltage_pu },
    { metric: 'Min voltage', unit: 'pu', base: baseSummary.minimum_voltage_pu, scenario: scenarioSummary.minimum_voltage_pu },
    { metric: 'Max line loading', unit: '%', base: baseSummary.maximum_line_loading, scenario: scenarioSummary.maximum_line_loading },
    { metric: 'Overloaded lines', unit: '', base: baseSummary.overloaded_lines, scenario: scenarioSummary.overloaded_lines },
  ];

  return specs.map((spec) => {
    const change = spec.scenario - spec.base;
    const changePercent =
      spec.base === 0 ? null : (change / spec.base) * 100;
    return {
      metric: spec.metric,
      unit: spec.unit,
      base: spec.base,
      scenario: spec.scenario,
      change,
      changePercent,
    };
  });
}

export function buildVoltageComparison(
  base: PowerFlowResult,
  scenario: PowerFlowResult,
): VoltageRow[] {
  const byId = (result: PowerFlowResult) =>
    new Map(result.buses.map((bus) => [bus.bus_id, bus.voltage_magnitude]));

  const baseMap = byId(base);
  const scenarioMap = byId(scenario);

  const rows: VoltageRow[] = [];
  baseMap.forEach((baseVoltage, busId) => {
    const scenarioVoltage = scenarioMap.get(busId);
    if (scenarioVoltage == null) return;
    const change = scenarioVoltage - baseVoltage;
    let classification: VoltageRow['classification'] = 'unchanged';
    if (Math.abs(change) >= 0.01) {
      const baseBad = baseVoltage > 1.05 || baseVoltage < 0.95;
      const scenarioBad = scenarioVoltage > 1.05 || scenarioVoltage < 0.95;
      if (baseBad && !scenarioBad) classification = 'improved';
      else if (!baseBad && scenarioBad) classification = 'violation';
      else if (baseBad && scenarioBad) classification = 'warning';
      else classification = 'warning';
    }
    rows.push({
      busId,
      base: baseVoltage,
      scenario: scenarioVoltage,
      change,
      classification,
    });
  });
  return rows.sort((a, b) => a.busId.localeCompare(b.busId));
}

export function buildLineComparison(
  base: PowerFlowResult,
  scenario: PowerFlowResult,
): LineRow[] {
  const byId = (result: PowerFlowResult) =>
    new Map(result.lines.map((line) => [line.line_id, line]));

  const baseMap = byId(base);
  const scenarioMap = byId(scenario);

  const rows: LineRow[] = [];
  baseMap.forEach((baseLine: LineResult, lineId: string) => {
    const scenarioLine = scenarioMap.get(lineId);
    if (!scenarioLine) return;
    rows.push({
      lineId,
      baseLoading: baseLine.loading_percentage,
      scenarioLoading: scenarioLine.loading_percentage,
      baseStatus: baseLine.status,
      scenarioStatus: scenarioLine.status,
      transition: baseLine.status !== scenarioLine.status,
    });
  });
  return rows.sort(
    (a, b) => b.scenarioLoading - a.scenarioLoading,
  );
}
