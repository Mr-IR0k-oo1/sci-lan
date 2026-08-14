import { useState } from 'react';
import { engineApi } from '../../api/engine';
import { describeError } from '../../lib/errors';
import { Button, Spinner } from '../ui';
import type { EngineComparisonResponse, GridModel } from '../../types';

interface CompareEnginesPanelProps {
  grid: GridModel | null;
}

export function CompareEnginesPanel({ grid }: CompareEnginesPanelProps) {
  const [data, setData] = useState<EngineComparisonResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runComparison = async () => {
    if (!grid) return;
    setRunning(true);
    setError(null);
    try {
      const response = await engineApi.compare({ grid });
      setData(response);
    } catch (caught) {
      setError(describeError(caught));
    } finally {
      setRunning(false);
    }
  };

  const engineLine = (name: string, info: { available: boolean; converged: boolean | null; engine_version: string | null; execution_time_ms: number | null; error: string | null } | null) => {
    if (!info) return `${name}: —`;
    if (!info.available) return `${name}: not available`;
    const status = info.converged ? 'converged' : info.converged === false ? 'not converged' : 'unknown';
    const parts = [`${name}: ${status}`];
    if (info.engine_version) parts.push(`v${info.engine_version}`);
    if (info.execution_time_ms !== null) parts.push(`${info.execution_time_ms} ms`);
    if (info.error) parts.push(info.error);
    return parts.join(' · ');
  };

  return (
    <div className="compare-engines-panel" data-testid="compare-engines">
      <div className="compare-controls">
        <Button variant="primary" disabled={!grid || running} onClick={() => void runComparison()}>
          {running ? 'Comparing…' : 'Compare Engines'}
        </Button>
      </div>

      {running ? <Spinner label="Running Python and Scilab…" /> : null}
      {error ? <p className="panel-error">{error}</p> : null}

      {data ? (
        <div className="compare-engines-result">
          <p className="compare-engine-line">{engineLine('Python', data.python)}</p>
          <p className="compare-engine-line">{engineLine('Scilab', data.scilab)}</p>

          {!data.scilab.available ? (
            <p className="panel-hint">
              Scilab is not available on this machine, so no cross-engine comparison could be
              performed.
            </p>
          ) : data.comparison ? (
            <div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Max difference</th>
                    <th>Tolerance</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Voltage (pu)</td>
                    <td>{data.comparison.voltage_difference_max}</td>
                    <td>≤ 0.0001</td>
                  </tr>
                  <tr>
                    <td>Angle (°)</td>
                    <td>{data.comparison.angle_difference_max}</td>
                    <td>≤ 0.001</td>
                  </tr>
                  <tr>
                    <td>Line flow (pu)</td>
                    <td>{data.comparison.line_flow_difference_max}</td>
                    <td>≤ 0.02</td>
                  </tr>
                </tbody>
              </table>
              <p className="compare-verdict">
                Engines match:{' '}
                <span className={data.comparison.within_tolerance ? 'status-ok' : 'status-bad'}>
                  {data.comparison.within_tolerance ? 'Yes' : 'No'}
                </span>
              </p>
            </div>
          ) : (
            <p className="panel-hint">
              Both engines ran, but one did not converge — no comparison computed.
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
