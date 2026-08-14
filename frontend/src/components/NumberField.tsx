import { useEffect, useState, type ReactNode } from 'react';

interface NumberFieldProps {
  label: string;
  value: number;
  min?: number;
  max?: number;
  step?: number;
  suffix?: string;
  onChange: (value: number) => void;
}

export function NumberField({
  label,
  value,
  min,
  max,
  step = 1,
  suffix,
  onChange,
}: NumberFieldProps) {
  const [text, setText] = useState(String(value));
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dirty) setText(String(value));
  }, [value, dirty]);

  const commit = () => {
    setDirty(false);
    if (text.trim() === '') {
      setError('Enter a valid number.');
      return;
    }
    const parsed = Number(text.replace(/,/g, '.'));
    if (!Number.isFinite(parsed)) {
      setError('Enter a valid number.');
      return;
    }
    if (min !== undefined && parsed < min) {
      setError(`Minimum value is ${min}.`);
      return;
    }
    if (max !== undefined && parsed > max) {
      setError(`Maximum value is ${max}.`);
      return;
    }
    setError(null);
    setText(String(parsed));
    onChange(parsed);
  };

  return (
    <div className="field">
      <label className="field-label" htmlFor={`nf-${label}`}>
        {label}
      </label>
      <div className="number-field">
        <input
          id={`nf-${label}`}
          type="number"
          inputMode="decimal"
          step={step}
          value={text}
          onChange={(event) => {
            setText(event.target.value);
            setDirty(true);
          }}
          onBlur={commit}
          onKeyDown={(event) => {
            if (event.key === 'Enter') commit();
          }}
          aria-invalid={error ? true : undefined}
        />
        {suffix ? <span className="field-suffix">{suffix}</span> : null}
      </div>
      {error ? <span className="field-error">{error}</span> : null}
    </div>
  );
}

interface SelectFieldProps<T extends string> {
  label: string;
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
}

export function SelectField<T extends string>({
  label,
  value,
  options,
  onChange,
}: SelectFieldProps<T>) {
  return (
    <div className="field">
      <label className="field-label" htmlFor={`sf-${label}`}>
        {label}
      </label>
      <select
        id={`sf-${label}`}
        value={value}
        onChange={(event) => onChange(event.target.value as T)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

interface TextFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

export function TextField({ label, value, onChange }: TextFieldProps) {
  const [text, setText] = useState(value);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (!dirty) setText(value);
  }, [value, dirty]);

  const commit = () => {
    setDirty(false);
    onChange(text);
  };

  return (
    <div className="field">
      <label className="field-label" htmlFor={`tf-${label}`}>
        {label}
      </label>
      <input
        id={`tf-${label}`}
        type="text"
        value={text}
        onChange={(event) => {
          setText(event.target.value);
          setDirty(true);
        }}
        onBlur={commit}
        onKeyDown={(event) => {
          if (event.key === 'Enter') commit();
        }}
      />
    </div>
  );
}

export function SliderField({
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
  const display = value ?? 0;
  return (
    <div className="field">
      <label className="field-label">
        {label} <span className="range-value">{display.toFixed(0)}</span>
        {value !== null ? ` ${suffix}` : ''}
      </label>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={display}
        onChange={(event) => {
          const next = Number(event.target.value);
          onChange(next);
        }}
      />
    </div>
  );
}

export function EmptyHint({ children }: { children: ReactNode }) {
  return <p className="panel-hint">{children}</p>;
}
