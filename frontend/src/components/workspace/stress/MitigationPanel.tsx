import { useState } from 'react';
import type { MitigationCandidate, MitigationTestResult } from '../../../types';
import { formatNumber, formatSigned } from '../../../lib/format';
import { Button, Spinner, StatusBadge } from '../../ui';
import { PlayIcon } from '../../icons';

interface MitigationPanelProps {
  candidates: MitigationCandidate[];
  tests: MitigationTestResult[];
  running: boolean;
  onRunAll: () => void;
  onRunCandidate: (candidateId: string) => void;
}

function MitigationTable({ test }: { test: MitigationTestResult }) {
  const improved = test.converged && test.after_score < test.before_score;
  return (
    <div className={`mitigation-test ${test.converged ? '' : 'mitigation-test-failed'}`}>
      <div className="mitigation-test-header">
        <strong>{test.mitigation_name}</strong>
        {!test.converged ? (
          <StatusBadge className="status-bad">Did not converge</StatusBadge>
        ) : (
          <StatusBadge className={improved ? 'status-ok' : 'status-warn'}>
            {test.after_classification || '—'}
          </StatusBadge>
        )}
      </div>
      {test.converged ? (
        <table className="data-table mitigation-scores">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Before</th>
              <th>After</th>
              <th>Change</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Stress score</td>
              <td>{formatNumber(test.before_score)}</td>
              <td>{formatNumber(test.after_score)}</td>
              <td className={improved ? 'status-ok' : 'status-warn'}>
                {formatSigned(test.after_score - test.before_score)}
              </td>
            </tr>
            {test.metric_changes.map((change) => (
              <tr key={change.metric}>
                <td>{change.metric}</td>
                <td>{`${formatNumber(change.before)}${change.unit ? ` ${change.unit}` : ''}`}</td>
                <td>{`${formatNumber(change.after)}${change.unit ? ` ${change.unit}` : ''}`}</td>
                <td className={change.improvement ? 'status-ok' : 'status-warn'}>
                  {change.improvement ? 'improved' : 'worse'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
      <p className="panel-hint">{test.notes}</p>
      {test.resolved_issues.length > 0 ? (
        <p className="mitigation-outcome">
          Resolved: {test.resolved_issues.map((issue) => issue.title).join(' · ')}
        </p>
      ) : null}
      {test.remaining_issues.length > 0 ? (
        <p className="mitigation-outcome mitigation-outcome-warn">
          Remaining: {test.remaining_issues.map((issue) => issue.title).join(' · ')}
        </p>
      ) : null}
      {test.new_issues.length > 0 ? (
        <p className="mitigation-outcome mitigation-outcome-bad">
          New: {test.new_issues.map((issue) => issue.title).join(' · ')}
        </p>
      ) : null}
    </div>
  );
}

export function MitigationPanel({
  candidates,
  tests,
  running,
  onRunAll,
  onRunCandidate,
}: MitigationPanelProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (candidates.length === 0) {
    return (
      <p className="panel-hint">
        No mitigation candidates were generated for this analysis. Try a grid with voltage, line, or
        generation stress conditions.
      </p>
    );
  }

  return (
    <div className="mitigation-panel">
      <div className="mitigation-actions">
        <Button variant="primary" icon={<PlayIcon />} onClick={onRunAll} disabled={running}>
          {running ? 'Running tests…' : `Test all (${candidates.length})`}
        </Button>
      </div>
      {running ? <Spinner label="Running mitigation tests…" /> : null}

      <ul className="mitigation-candidates">
        {candidates.map((candidate) => {
          const test = tests.find((item) => item.mitigation_id === candidate.id);
          const isOpen = expanded === candidate.id;
          return (
            <li key={candidate.id} className="mitigation-candidate">
              <div className="mitigation-candidate-header">
                <button
                  type="button"
                  className="mitigation-candidate-title"
                  onClick={() => setExpanded(isOpen ? null : candidate.id)}
                >
                  <span>{candidate.name}</span>
                  {test ? (
                    <StatusBadge className="status-idle">
                      {formatNumber(test.after_score)}
                    </StatusBadge>
                  ) : null}
                </button>
                <Button
                  variant="secondary"
                  disabled={running}
                  onClick={() => onRunCandidate(candidate.id)}
                >
                  Test
                </Button>
              </div>
              <p className="panel-hint">{candidate.description}</p>
              {isOpen && test ? <MitigationTable test={test} /> : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
