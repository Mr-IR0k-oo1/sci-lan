import { useState } from 'react';
import type { ComponentSelection } from '../../types';
import { useStress } from '../../state/StressContext';
import { download } from '../../api/client';
import { GridHealthPanel } from './stress/GridHealthPanel';
import { IssueExplorerPanel } from './stress/IssueExplorerPanel';
import { RecommendationsPanel } from './stress/RecommendationsPanel';
import { MitigationPanel } from './stress/MitigationPanel';
import { Button } from '../ui';

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
  const [exporting, setExporting] = useState<'json' | 'csv' | null>(null);

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

  const handleExport = async (format: 'json' | 'csv') => {
    setExporting(format);
    try {
      await download(`/analyses/${record.id}/export?format=${format}`, `${record.id}.${format}`);
    } finally {
      setExporting(null);
    }
  };

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
        <span className="results-export">
          <Button
            variant="ghost"
            disabled={exporting !== null}
            onClick={() => void handleExport('json')}
          >
            {exporting === 'json' ? 'Exporting…' : 'Export JSON'}
          </Button>
          <Button
            variant="ghost"
            disabled={exporting !== null}
            onClick={() => void handleExport('csv')}
          >
            {exporting === 'csv' ? 'Exporting…' : 'Export CSV'}
          </Button>
        </span>
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
