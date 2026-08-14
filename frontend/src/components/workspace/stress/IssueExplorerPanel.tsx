import type { ComponentSelection, StressIssue } from '../../../types';
import { formatNumber } from '../../../lib/format';
import { severityClass } from '../../../lib/stress';
import { StatusBadge } from '../../ui';
import { ErrorIcon, WarningIcon } from '../../icons';

const CATEGORY_LABELS: Record<string, string> = {
  VOLTAGE_STRESS: 'Voltage',
  TRANSMISSION_STRESS: 'Transmission',
  GENERATION_BALANCE: 'Generation',
  RENEWABLE_IMPACT: 'Renewable',
};

interface IssueExplorerPanelProps {
  issues: StressIssue[];
  onSelect: (selection: ComponentSelection | null) => void;
}

function IssueEvidence({ evidence }: { evidence: Record<string, number | string> }) {
  const entries = Object.entries(evidence);
  if (entries.length === 0) return null;
  return (
    <ul className="issue-evidence">
      {entries.map(([key, value]) => (
        <li key={key}>
          <span className="issue-evidence-key">{key}:</span>{' '}
          {typeof value === 'number' ? formatNumber(value) : value}
        </li>
      ))}
    </ul>
  );
}

export function IssueExplorerPanel({ issues, onSelect }: IssueExplorerPanelProps) {
  if (issues.length === 0) {
    return <p className="panel-hint">No issues detected. The grid is operating within configured limits.</p>;
  }

  return (
    <ul className="stress-issues">
      {issues.map((issue) => {
        const canSelect =
          issue.affected_component_id && issue.affected_component_type === 'BUS';
        return (
          <li key={issue.id} className={`stress-issue stress-issue-${issue.severity.toLowerCase()}`}>
            <div className="stress-issue-header">
              <span className="issue-icon" aria-hidden="true">
                {issue.severity === 'CRITICAL' ? <ErrorIcon /> : <WarningIcon />}
              </span>
              <strong>{issue.title}</strong>
              <StatusBadge className={severityClass(issue.severity)}>
                {issue.severity}
              </StatusBadge>
            </div>
            <p className="stress-issue-description">{issue.description}</p>
            <div className="stress-issue-meta">
              <span className="status-badge status-idle">
                {CATEGORY_LABELS[issue.category] ?? issue.category}
              </span>
              {issue.affected_component_id ? (
                <span className="status-badge status-idle">
                  {issue.affected_component_type} {issue.affected_component_id}
                </span>
              ) : null}
              {canSelect ? (
                <button
                  type="button"
                  className="link-button"
                  onClick={() =>
                    onSelect({
                      kind: 'bus',
                      id: issue.affected_component_id as string,
                    })
                  }
                >
                  Locate
                </button>
              ) : null}
            </div>
            <IssueEvidence evidence={issue.evidence} />
          </li>
        );
      })}
    </ul>
  );
}
