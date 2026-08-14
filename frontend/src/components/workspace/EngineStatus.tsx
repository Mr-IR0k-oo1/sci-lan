import { useEffect, useState } from 'react';
import { engineApi } from '../../api/engine';
import { useAnalysis } from '../../state/AnalysisContext';
import { StatusBadge } from '../ui';
import type { EngineRegistry, ScilabStatus } from '../../types';

const ENGINE_OPTIONS = [
  { value: 'auto', label: 'Auto' },
  { value: 'python', label: 'Python' },
  { value: 'scilab', label: 'Scilab' },
];

function resolvedEngineLabel(engine: string, scilabAvailable: boolean): string {
  if (engine !== 'auto') return engine;
  return scilabAvailable ? 'scilab (auto)' : 'python (auto)';
}

export function EngineStatus() {
  const { engine, setEngine } = useAnalysis();
  const [registry, setRegistry] = useState<EngineRegistry | null>(null);
  const [scilab, setScilab] = useState<ScilabStatus | null>(null);

  useEffect(() => {
    void engineApi
      .status()
      .then(setRegistry)
      .catch(() => setRegistry(null));
    void engineApi
      .scilabStatus()
      .then(setScilab)
      .catch(() => setScilab(null));
  }, []);

  const scilabAvailable = scilab?.available ?? false;
  const scilabInfo = registry?.engines.find((item) => item.name === 'scilab');

  return (
    <div className="engine-status" data-testid="engine-status">
      <label className="field inline-field">
        <span className="field-label">Engine</span>
        <select
          value={engine}
          onChange={(event) => setEngine(event.target.value)}
          aria-label="Analysis engine"
        >
          {ENGINE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value} disabled={option.value === 'scilab' && !scilabAvailable}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <span
        className={`engine-status-dot ${scilabAvailable ? 'engine-status-ok' : 'engine-status-missing'}`}
        title={
          scilab
            ? `Scilab ${scilab.version ?? 'unknown version'}${scilab.executable_path ? `\n${scilab.executable_path}` : ''}\n${scilab.message}`
            : 'Scilab status unavailable'
        }
        aria-label={`Scilab ${scilabAvailable ? 'available' : 'unavailable'}`}
      />

      <StatusBadge className={scilabAvailable ? 'status-ok' : 'status-idle'}>
        {resolvedEngineLabel(engine, scilabAvailable)}
      </StatusBadge>

      {!scilabAvailable && scilabInfo ? (
        <span className="engine-missing-hint" title={scilab?.message}>
          Scilab not found
        </span>
      ) : null}
    </div>
  );
}
