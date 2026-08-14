import type { StressAnalysisResult } from '../../../types';
import { formatNumber, formatPercent } from '../../../lib/format';
import {
  impactLevelClass,
  impactLevelLabel,
  SEVERITY_LABELS,
  stressLevelClass,
} from '../../../lib/stress';
import { Section, StatusBadge } from '../../ui';

function ComponentBar({ label, score, reason }: { label: string; score: number; reason: string }) {
  const colorClass =
    score >= 70 ? 'bar-violation' : score >= 40 ? 'bar-warning' : 'bar-loading';
  return (
    <div className="stress-component">
      <div className="stress-component-head">
        <span className="bar-label">{label}</span>
        <span className="bar-value">{formatNumber(score)}/100</span>
      </div>
      <div className="bar-track">
        <span className={`bar-fill ${colorClass}`} style={{ width: `${Math.min(100, score)}%` }} />
      </div>
      <p className="stress-component-reason">{reason}</p>
    </div>
  );
}

export function GridHealthPanel({ stress }: { stress: StressAnalysisResult }) {
  const { score, generation, renewable, issues } = stress;
  const critical = issues.filter((issue) => issue.severity === 'CRITICAL').length;
  const warning = issues.filter((issue) => issue.severity === 'WARNING').length;

  return (
    <div className="stress-health">
      <div className="stress-score-card">
        <span className="stress-score-value">{formatNumber(score.overall_score)}</span>
        <StatusBadge className={stressLevelClass(score.classification)}>
          {score.classification}
        </StatusBadge>
        <p className="stress-score-summary">
          {score.reasons.length > 0 ? score.reasons[0] : 'No stress conditions detected.'}
        </p>
        <div className="stress-counts">
          <StatusBadge className="status-bad">{critical} critical</StatusBadge>
          <StatusBadge className="status-warn">{warning} warning</StatusBadge>
        </div>
      </div>

      <Section title="Component scores">
        {score.components.map((component) => (
          <ComponentBar
            key={component.key}
            label={component.label}
            score={component.score}
            reason={component.reason}
          />
        ))}
      </Section>

      <Section title="Generation balance">
        <table className="metrics-table">
          <tbody>
            <tr>
              <td>Total generation</td>
              <td>{formatNumber(generation.total_generation_mw)} MW</td>
            </tr>
            <tr>
              <td>Total load</td>
              <td>{formatNumber(generation.total_load_mw)} MW</td>
            </tr>
            <tr>
              <td>Total losses</td>
              <td>{formatNumber(generation.total_losses_mw)} MW</td>
            </tr>
            <tr>
              <td>Slack output</td>
              <td>{formatNumber(generation.slack_generation_mw)} MW</td>
            </tr>
            <tr>
              <td>Available reserve</td>
              <td>{formatNumber(generation.available_reserve_mw)} MW</td>
            </tr>
            <tr>
              <td>Renewable</td>
              <td>{formatNumber(generation.renewable_generation_mw)} MW</td>
            </tr>
          </tbody>
        </table>
        {generation.detections.length > 0 ? (
          <ul className="stress-detections">
            {generation.detections.map((detection) => (
              <li key={detection}>
                <StatusBadge className="status-warn">{detection}</StatusBadge>
              </li>
            ))}
          </ul>
        ) : null}
      </Section>

      <Section title="Renewable impact">
        <div className="stress-renewable">
          <StatusBadge className={impactLevelClass(renewable.impact_level)}>
            {impactLevelLabel(renewable.impact_level)}
          </StatusBadge>
          <span>
            {formatPercent(renewable.renewable_penetration)} penetration ·{' '}
            {formatNumber(renewable.renewable_generation_mw)} MW
          </span>
        </div>
        {renewable.reason ? <p className="panel-hint">{renewable.reason}</p> : null}
        {renewable.new_violations.length > 0 ? (
          <p className="panel-hint stress-new-violations">
            New: {renewable.new_violations.join(', ')}
          </p>
        ) : null}
        {renewable.resolved_violations.length > 0 ? (
          <p className="panel-hint">
            Resolved: {renewable.resolved_violations.join(', ')}
          </p>
        ) : null}
      </Section>

      <Section title="Voltage stress">
        <table className="data-table">
          <thead>
            <tr>
              <th>Bus</th>
              <th>Voltage (pu)</th>
              <th>Classification</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            {stress.buses.map((bus) => (
              <tr key={bus.bus_id}>
                <td>{bus.bus_id}</td>
                <td>{formatNumber(bus.voltage_pu, 3)}</td>
                <td>{SEVERITY_LABELS[bus.severity]}</td>
                <td>
                  <StatusBadge className={bus.severity === 'NORMAL' ? 'status-ok' : 'status-warn'}>
                    {bus.classification}
                  </StatusBadge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}
