import { useEffect, useRef } from 'react';
import { useWhatIf, type WhatIfValues } from '../../state/WhatIfContext';
import { Button, Section, Spinner } from '../ui';
import { formatNumber } from '../../lib/format';

function SliderRow({
  label,
  value,
  min,
  max,
  step,
  suffix,
  onChange,
}: {
  label: string;
  value: number | null;
  min: number;
  max: number;
  step: number;
  suffix: string;
  onChange: (value: number | null) => void;
}) {
  return (
    <div className="field">
      <label className="field-label" htmlFor={`whatif-${label}`}>
        {label}
        <span className="range-value">{value !== null ? `${value.toFixed(0)} ${suffix}` : 'off'}</span>
      </label>
      <div className="whatif-slider-row">
        <input
          id={`whatif-${label}`}
          type="range"
          min={min}
          max={max}
          step={step}
          value={value ?? 0}
          onChange={(event) => onChange(Number(event.target.value))}
        />
        {value !== null ? (
          <button
            type="button"
            className="link-button"
            onClick={() => onChange(null)}
            aria-label={`Reset ${label}`}
          >
            reset
          </button>
        ) : null}
      </div>
    </div>
  );
}

export function WhatIfPanel() {
  const { active, values, result, status, error, setValue, run, clear } = useWhatIf();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!active) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => void run(), 400);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [active, values, run]);

  const setScalar = (key: keyof WhatIfValues) => (value: number | null) => setValue(key, value);

  return (
    <Section title="What-if">
      <p className="panel-hint">
        Adjust inputs to preview a scenario. The base grid is never modified.
      </p>

      <SliderRow
        label="Solar output"
        value={values.solar}
        min={0}
        max={300}
        step={5}
        suffix="MW"
        onChange={setScalar('solar')}
      />
      <SliderRow
        label="Wind output"
        value={values.wind}
        min={0}
        max={300}
        step={5}
        suffix="MW"
        onChange={setScalar('wind')}
      />
      <SliderRow
        label="Battery discharge"
        value={values.battery}
        min={-100}
        max={100}
        step={5}
        suffix="MW"
        onChange={setScalar('battery')}
      />
      <SliderRow
        label="Load scale"
        value={values.loadScale}
        min={0.5}
        max={2}
        step={0.05}
        suffix="×"
        onChange={setScalar('loadScale')}
      />

      {error ? <p className="panel-error">{error}</p> : null}

      {active ? (
        <div className="whatif-actions">
          <Button variant="primary" onClick={() => void run()}>
            {status === 'running' ? 'Analyzing…' : 'Run now'}
          </Button>
          <Button variant="danger" onClick={clear}>
            Clear
          </Button>
        </div>
      ) : null}

      {status === 'running' ? <Spinner label="Running temporary analysis…" /> : null}

      {result ? (
        <div className="whatif-result">
          <div className="panel-section-header">
            <h3 className="whatif-title">
              What-if result <span className="temporary-badge">TEMPORARY</span>
            </h3>
          </div>
          <div className="impact-score-card">
            <span className="impact-score-value">{formatNumber(result.impact_score?.score ?? 0)}</span>
            <span className="impact-score-grade">Grade {result.impact_score?.grade ?? '—'}</span>
            <p className="impact-score-message">{result.impact_score?.message ?? ''}</p>
          </div>
          <ul>
            <li>
              Generation: {formatNumber(result.summary?.total_generation_mw ?? 0)} MW
            </li>
            <li>
              Renewable: {formatNumber(result.summary?.renewable_generation_mw ?? 0)} MW
            </li>
            <li>Load: {formatNumber(result.summary?.total_load_mw ?? 0)} MW</li>
            <li>Losses: {formatNumber(result.summary?.total_losses_mw ?? 0)} MW</li>
            <li>
              Max line loading:{' '}
              {formatNumber(result.summary?.maximum_line_loading ?? 0)}%
            </li>
          </ul>
        </div>
      ) : null}
    </Section>
  );
}
