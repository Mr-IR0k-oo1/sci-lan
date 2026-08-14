import { useMemo } from 'react';
import { BarChart } from './BarChart';
import type { LineRow, MetricRow, VoltageRow } from '../../lib/comparison';

export function ComparisonChart({ title, rows }: { title: string; rows: MetricRow[] }) {
  const data = useMemo(
    () =>
      rows.map((row) => ({
        label: row.metric,
        base: row.base,
        scenario: row.scenario,
      })),
    [rows],
  );
  return (
    <div className="comparison-chart">
      <BarChart
        title={`${title} · Base`}
        data={data.map((d) => ({
          label: d.label,
          value: d.base,
          className: 'bar-base',
        }))}
      />
      <BarChart
        title={`${title} · Scenario`}
        data={data.map((d) => ({
          label: d.label,
          value: d.scenario,
          className: 'bar-scenario',
        }))}
      />
    </div>
  );
}

export function VoltageComparisonChart({ rows }: { rows: VoltageRow[] }) {
  const data = useMemo(
    () =>
      rows.map((row) => ({
        label: row.busId,
        value: row.scenario,
        className: row.classification,
      })),
    [rows],
  );
  return <BarChart title="Voltage magnitude (pu)" data={data} max={1.2} />;
}

export function LineComparisonChart({ rows }: { rows: LineRow[] }) {
  const data = useMemo(
    () =>
      rows.map((row) => ({
        label: row.lineId,
        value: row.scenarioLoading,
        className: row.scenarioStatus === 'OVERLOADED' ? 'bar-overload' : 'bar-loading',
      })),
    [rows],
  );
  return <BarChart title="Line loading (%)" data={data} max={100} />;
}
