import { useState } from 'react';
import { useScenario } from '../../state/ScenarioContext';
import { Button, Section, Spinner, StatusBadge } from '../ui';
import { RefreshIcon, TrashIcon } from '../icons';
import { formatNumber } from '../../lib/format';

function runBadge(state: string | undefined) {
  switch (state) {
    case 'running':
      return <Spinner label="Analyzing…" />;
    case 'success':
      return <StatusBadge className="status-ok">✓ analyzed</StatusBadge>;
    case 'failed':
      return <StatusBadge className="status-bad">not converged</StatusBadge>;
    case 'error':
      return <StatusBadge className="status-bad">error</StatusBadge>;
    default:
      return <StatusBadge className="status-idle">not run</StatusBadge>;
  }
}

export function ScenarioPanel() {
  const {
    scenarios,
    activeScenario,
    inScenarioMode,
    results,
    runStates,
    runErrors,
    refresh,
    editScenario,
    createScenario,
    duplicateScenario,
    deleteScenario,
    saveDraft,
    exitScenarioMode,
    runScenario,
    scenarioError,
  } = useScenario();
  const [name, setName] = useState('');

  return (
    <>
      {inScenarioMode ? (
        <Section title="Scenario mode">
          <p className="panel-hint">
            Editing <strong>{activeScenario?.name}</strong>. Changes below are applied to the
            scenario copy; the base grid stays untouched.
          </p>
          <div className="scenario-mode-actions">
            <Button variant="primary" onClick={() => void saveDraft()}>
              Save Scenario
            </Button>
            <Button onClick={exitScenarioMode}>Exit</Button>
          </div>
        </Section>
      ) : null}

      <Section
        title="Scenarios"
        action={
          <Button variant="ghost" icon={<RefreshIcon />} onClick={() => void refresh()}>
            Refresh
          </Button>
        }
      >
        <div className="scenario-create">
          <input
            type="text"
            placeholder="Scenario name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            aria-label="New scenario name"
          />
          <Button
            variant="primary"
            disabled={!name.trim()}
            onClick={() => {
              void createScenario(name.trim());
              setName('');
            }}
          >
            Create
          </Button>
        </div>

        {scenarioError ? <p className="panel-error">{scenarioError}</p> : null}

        {scenarios.length === 0 ? (
          <p className="panel-hint">
            Scenarios are copies of the grid you can modify and analyze without touching the base.
          </p>
        ) : (
          <ul className="scenario-list">
            {scenarios.map((scenario) => {
              const result = results[scenario.id];
              const runError = runErrors[scenario.id];
              const isActive = activeScenario?.id === scenario.id;
              return (
                <li
                  key={scenario.id}
                  className={`scenario-item${isActive ? ' scenario-item-active' : ''}`}
                >
                  <div className="scenario-item-header">
                    <span>{scenario.name}</span>
                    {runBadge(runStates[scenario.id])}
                  </div>
                  {result ? (
                    <p className="scenario-result">
                      Impact score:{' '}
                      <strong>
                        {formatNumber(result.impact_score?.score ?? 0)}
                      </strong>{' '}
                      ({result.impact_score?.grade ?? '—'}) · Load{' '}
                      {formatNumber(result.summary?.total_load_mw ?? 0)} MW
                    </p>
                  ) : null}
                  {runError ? <p className="panel-error">{runError}</p> : null}
                  <div className="scenario-actions">
                    <Button variant="primary" onClick={() => void runScenario(scenario.id)}>
                      Run
                    </Button>
                    <Button onClick={() => void editScenario(scenario.id)}>Edit</Button>
                    <Button onClick={() => void duplicateScenario(scenario.id)}>Duplicate</Button>
                    <Button
                      variant="danger"
                      icon={<TrashIcon />}
                      onClick={() => void deleteScenario(scenario.id)}
                    >
                      Delete
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Section>
    </>
  );
}
