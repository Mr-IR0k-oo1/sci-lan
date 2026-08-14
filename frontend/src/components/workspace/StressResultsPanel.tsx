import { useState } from 'react';
import type { ComponentSelection } from '../../types';
import { useStress } from '../../state/StressContext';
import { GridHealthPanel } from './stress/GridHealthPanel';
import { IssueExplorerPanel } from './stress/IssueExplorerPanel';
import { RecommendationsPanel } from './stress/RecommendationsPanel';
import { MitigationPanel } from './stress/MitigationPanel';

type Tab = 'health' | 'issues' | 'recommendations' | 'mitigations';

const TABS: { key: Tab; label: string }[] = [
  { key: 'health', label: 'Grid Health' },
  { key: 'issues', label: 'Issues' },
  { key: 'recommendations', label: 'Recommendations' },
  { key: 'mitigations', label: 'Mitigations' },
];

interface StressResultsPanelProps {
  onSelect: (selection: ComponentSelection | null) => void;
}

export function StressResultsPanel({ onSelect }: StressResultsPanelProps) {
  const { status, record, error, runMitigationTests } = useStress();
  const [tab, setTab] = useState<Tab>('health');

  if (!record) {
    return (
      <div className="results-panel" data-testid="stress-results">
        <div className="results-tabs">
          {TABS.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              className={`results-tab${tab === key ? ' results-tab-active' : ''}`}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </div>
        <p className="panel-hint">
          {status === 'error' || status === 'failed'
            ? error ?? 'Stress analysis failed.'
            : 'Run a stress analysis to see grid health, issues, recommendations, and mitigation options.'}
        </p>
      </div>
    );
  }

  const stress = record.stress;
  const issueCount = stress.issues.length;

  const tabLabel = (key: Tab) =>
    key === 'issues' && issueCount > 0 ? `Issues (${issueCount})` : TABS.find((t) => t.key === key)?.label ?? key;

  return (
    <div className="results-panel" data-testid="stress-results">
      <div className="results-tabs">
        {TABS.map(({ key }) => (
          <button
            key={key}
            type="button"
            className={`results-tab${tab === key ? ' results-tab-active' : ''}`}
            onClick={() => setTab(key)}
          >
            {tabLabel(key)}
          </button>
        ))}
      </div>

      {tab === 'health' ? <GridHealthPanel stress={stress} /> : null}
      {tab === 'issues' ? <IssueExplorerPanel issues={stress.issues} onSelect={onSelect} /> : null}
      {tab === 'recommendations' ? (
        <RecommendationsPanel recommendations={record.recommendations} />
      ) : null}
      {tab === 'mitigations' ? (
        <MitigationPanel
          candidates={record.mitigation_candidates}
          tests={record.mitigation_tests}
          running={status === 'running'}
          onRunAll={() => void runMitigationTests()}
          onRunCandidate={(id) => void runMitigationTests([id])}
        />
      ) : null}
    </div>
  );
}
