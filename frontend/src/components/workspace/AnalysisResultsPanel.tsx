import { useMemo, useState } from 'react';
import { useScenario } from '../../state/ScenarioContext';
import { buildLineComparison, buildMetricComparison, buildVoltageComparison } from '../../lib/comparison';
import {
  BUS_STATUS_LABELS,
  LINE_STATUS_LABELS,
  busStatusClass,
  formatNumber,
  formatPercent,
  formatSigned,
  lineStatusClass,
  voltageClass,
} from '../../lib/format';
import { StatusBadge } from '../ui';
import { ComparisonChart, LineComparisonChart, VoltageComparisonChart } from '../charts/ComparisonChart';
import type { AnalysisStatus } from '../../state/AnalysisContext';
import type { PowerFlowResult } from '../../types';

type Tab = 'summary' | 'voltage' | 'lines' | 'compare';

interface AnalysisResultsPanelProps {
  result: PowerFlowResult | null;
  status: AnalysisStatus;
  error: string | null;
}

function SummaryTab({ result }: { result: PowerFlowResult }) {
  const summary = result.summary;
  const impact = result.impact_score;
  return (
    <div className="results-summary">
      {impact ? (
        <div className="impact-score-card">
          <span className="impact-score-value">{formatNumber(impact.score)}</span>
          <span className="impact-score-grade">Grade {impact.grade}</span>
          <p className="impact-score-message">{impact.message}</p>
          {Object.entries(impact.categories).length > 0 ? (
            <ul className="impact-categories">
              {Object.entries(impact.categories).map(([key, category]) => (
                <li key={key}>
                  {key}: {formatNumber(category.score)}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
      <table className="metrics-table">
        <tbody>
          <tr>
            <td>Total generation</td>
            <td>{formatNumber(summary?.total_generation_mw ?? 0)} MW</td>
          </tr>
          <tr>
            <td>Renewable generation</td>
            <td>{formatNumber(summary?.renewable_generation_mw ?? 0)} MW</td>
          </tr>
          <tr>
            <td>Total load</td>
            <td>{formatNumber(summary?.total_load_mw ?? 0)} MW</td>
          </tr>
          <tr>
            <td>Total losses</td>
            <td>{formatNumber(summary?.total_losses_mw ?? 0)} MW</td>
          </tr>
          <tr>
            <td>Min voltage</td>
            <td>{formatNumber(summary?.minimum_voltage_pu ?? 0)} pu</td>
          </tr>
          <tr>
            <td>Max voltage</td>
            <td>{formatNumber(summary?.maximum_voltage_pu ?? 0)} pu</td>
          </tr>
          <tr>
            <td>Max line loading</td>
            <td>{formatPercent(summary?.maximum_line_loading ?? 0)}</td>
          </tr>
          <tr>
            <td>Overloaded lines</td>
            <td>{summary?.overloaded_lines ?? 0}</td>
          </tr>
          <tr>
            <td>Iterations</td>
            <td>{result.iterations}</td>
          </tr>
          <tr>
            <td>Execution time</td>
            <td>{formatNumber(result.execution_time_ms, 2)} ms</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function VoltageTab({ result }: { result: PowerFlowResult }) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Bus</th>
          <th>Voltage (pu)</th>
          <th>Angle (°)</th>
          <th>P (MW)</th>
          <th>Q (MVAr)</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {result.buses.map((bus) => (
          <tr key={bus.bus_id}>
            <td>{bus.bus_id}</td>
            <td className={voltageClass(bus.voltage_magnitude)}>
              {formatNumber(bus.voltage_magnitude, 3)}
            </td>
            <td>{formatNumber(bus.voltage_angle, 2)}</td>
            <td>{formatNumber(bus.active_power)}</td>
            <td>{formatNumber(bus.reactive_power)}</td>
            <td>
              <StatusBadge className={busStatusClass(bus.status)}>
                {BUS_STATUS_LABELS[bus.status]}
              </StatusBadge>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function LinesTab({ result }: { result: PowerFlowResult }) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Line</th>
          <th>From</th>
          <th>To</th>
          <th>P from (MW)</th>
          <th>Loading</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {result.lines.map((line) => (
          <tr key={line.line_id}>
            <td>{line.line_id}</td>
            <td>{line.from_bus}</td>
            <td>{line.to_bus}</td>
            <td>{formatNumber(line.active_power_from)}</td>
            <td>
              <span className="bar-track bar-track-inline">
                <span
                  className={`bar-fill ${line.status === 'OVERLOADED' ? 'bar-overload' : 'bar-loading'}`}
                  style={{ width: `${Math.min(100, line.loading_percentage)}%` }}
                />
              </span>
              {formatPercent(line.loading_percentage)}
            </td>
            <td>
              <StatusBadge className={lineStatusClass(line.status)}>
                {LINE_STATUS_LABELS[line.status]}
              </StatusBadge>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function CompareTab({ base }: { base: PowerFlowResult | null }) {
  const { scenarios, results, runStates, runScenario } = useScenario();
  const [selectedId, setSelectedId] = useState<string>('');
  const selected = results[selectedId];

  if (scenarios.length === 0) {
    return <p className="panel-hint">Create and run a scenario to compare it with the base grid.</p>;
  }

  const scenario = scenarios.find((item) => item.id === selectedId);

  return (
    <div>
      <div className="compare-controls">
        <div className="field compare-select">
          <label className="field-label" htmlFor="compare-select">
            Scenario
          </label>
          <select
            id="compare-select"
            value={selectedId}
            onChange={(event) => setSelectedId(event.target.value)}
          >
            <option value="">Select a scenario…</option>
            {scenarios.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </div>
        {scenario ? (
          <button type="button" className="btn btn-primary" onClick={() => void runScenario(scenario.id)}>
            Run {runStates[scenario.id] === 'running' ? '…' : ''}
          </button>
        ) : null}
      </div>

      {selected ? (
        <CompareResults base={base} scenario={selected} />
      ) : selectedId ? (
        <p className="panel-hint">Run this scenario first to see the comparison.</p>
      ) : null}
    </div>
  );
}

function CompareResults({
  base,
  scenario,
}: {
  base: PowerFlowResult | null;
  scenario: PowerFlowResult;
}) {
  const metricRows = useMemo(
    () => (base ? buildMetricComparison(base, scenario) : []),
    [base, scenario],
  );
  const voltageRows = useMemo(
    () => (base ? buildVoltageComparison(base, scenario) : []),
    [base, scenario],
  );
  const lineRows = useMemo(
    () => (base ? buildLineComparison(base, scenario) : []),
    [base, scenario],
  );

  if (!base) {
    return (
      <p className="panel-hint">
        Run the base analysis first so there is something to compare against.
      </p>
    );
  }

  return (
    <div>
      <ComparisonChart title="Metrics" rows={metricRows} />
      <table className="data-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Base</th>
            <th>Scenario</th>
            <th>Change</th>
          </tr>
        </thead>
        <tbody>
          {metricRows.map((row) => (
            <tr key={row.metric}>
              <td>{row.metric}</td>
              <td>{`${formatNumber(row.base)}${row.unit ? ` ${row.unit}` : ''}`}</td>
              <td>{`${formatNumber(row.scenario)}${row.unit ? ` ${row.unit}` : ''}`}</td>
              <td>
                {formatSigned(row.change)}
                {row.changePercent !== null ? ` (${formatSigned(row.changePercent, 1)}%)` : ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <VoltageComparisonChart rows={voltageRows} />
      <LineComparisonChart rows={lineRows} />
    </div>
  );
}

export function AnalysisResultsPanel({ result, status, error }: AnalysisResultsPanelProps) {
  const [tab, setTab] = useState<Tab>('summary');

  if (!result) {
    return (
      <div className="results-panel">
        <div className="results-tabs">
          {(['summary', 'voltage', 'lines', 'compare'] as Tab[]).map((key) => (
            <button
              key={key}
              type="button"
              className={`results-tab${tab === key ? ' results-tab-active' : ''}`}
              onClick={() => setTab(key)}
            >
              {key[0].toUpperCase() + key.slice(1)}
            </button>
          ))}
        </div>
        <p className="panel-hint">
          {status === 'failed' || status === 'error'
            ? error ?? 'Analysis failed.'
            : 'Run an analysis to see results here.'}
        </p>
      </div>
    );
  }

  return (
    <div className="results-panel">
      <div className="results-tabs">
        {(['summary', 'voltage', 'lines', 'compare'] as Tab[]).map((key) => (
          <button
            key={key}
            type="button"
            className={`results-tab${tab === key ? ' results-tab-active' : ''}`}
            onClick={() => setTab(key)}
          >
            {key[0].toUpperCase() + key.slice(1)}
          </button>
        ))}
      </div>
      {tab === 'summary' ? <SummaryTab result={result} /> : null}
      {tab === 'voltage' ? <VoltageTab result={result} /> : null}
      {tab === 'lines' ? <LinesTab result={result} /> : null}
      {tab === 'compare' ? <CompareTab base={result} /> : null}
    </div>
  );
}
