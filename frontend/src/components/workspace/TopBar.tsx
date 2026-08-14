import { useGrid } from '../../state/GridContext';
import { useAnalysis } from '../../state/AnalysisContext';
import { useStress } from '../../state/StressContext';
import { Button, Spinner } from '../ui';
import { PlayIcon, PlusIcon, SaveIcon } from '../icons';

export function TopBar() {
  const {
    gridId,
    grid,
    dirty,
    saving,
    loading,
    availableGridIds,
    loadGrid,
    createNewGrid,
    saveGrid,
  } = useGrid();
  const { status, runAnalysis, error } = useAnalysis();
  const stress = useStress();

  const running = status === 'validating' || status === 'running';
  const stressRunning = stress.status === 'running';

  return (
    <header className="topbar">
      <h1 className="app-title">GridFlex</h1>

      <div className="topbar-controls">
        <label className="field inline-field">
          <span className="field-label">Grid</span>
          <select
            value={gridId ?? ''}
            onChange={(event) => {
              if (event.target.value) void loadGrid(event.target.value);
            }}
            aria-label="Select grid"
          >
            {gridId ? null : <option value="">Select…</option>}
            {availableGridIds.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </label>

        <Button variant="secondary" icon={<PlusIcon />} onClick={() => void createNewGrid()}>
          New
        </Button>

        <span className="grid-name">
          {grid?.name ?? 'No grid'}
          {dirty ? <span className="dirty-dot" aria-label="Unsaved changes" /> : null}
        </span>

        <Button
          variant="secondary"
          icon={<SaveIcon />}
          disabled={!gridId || !dirty || saving}
          onClick={() => void saveGrid()}
        >
          {saving ? 'Saving…' : 'Save'}
        </Button>

        <Button variant="primary" icon={<PlayIcon />} disabled={!gridId || running} onClick={() => void runAnalysis()}>
          {running ? 'Analyzing…' : 'Run Analysis'}
        </Button>

        <Button
          variant="secondary"
          icon={<PlayIcon />}
          disabled={!gridId || stressRunning}
          onClick={() => void stress.runStress()}
        >
          {stressRunning ? 'Stress…' : 'Stress'}
        </Button>
      </div>

      {loading ? (
        <p className="topbar-error" role="status">
          <Spinner label="Loading grid…" />
        </p>
      ) : null}
      {status === 'failed' || status === 'error' ? (
        <p className="topbar-error" role="alert">
          {error}
        </p>
      ) : null}
      {stress.error ? (
        <p className="topbar-error" role="alert">
          {stress.error}
        </p>
      ) : null}
    </header>
  );
}
