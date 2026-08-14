import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { analysisApi } from '../api/analysis';
import { describeError } from '../lib/errors';
import type { PowerFlowResult } from '../types';
import { useGrid } from './GridContext';

export interface WhatIfValues {
  solar: number | null;
  wind: number | null;
  battery: number | null;
  loadScale: number | null;
}

export type WhatIfStatus = 'idle' | 'running' | 'success' | 'failed';

interface WhatIfContextValue {
  active: boolean;
  values: WhatIfValues;
  result: PowerFlowResult | null;
  status: WhatIfStatus;
  error: string | null;
  setValue: (key: keyof WhatIfValues, value: number | null) => void;
  run: () => Promise<void>;
  clear: () => void;
}

const WhatIfContext = createContext<WhatIfContextValue | null>(null);
const EMPTY_VALUES: WhatIfValues = { solar: null, wind: null, battery: null, loadScale: null };

export function WhatIfProvider({ children }: { children: ReactNode }) {
  const { gridId, dirty, saveGrid } = useGrid();
  const [values, setValues] = useState<WhatIfValues>(EMPTY_VALUES);
  const [result, setResult] = useState<PowerFlowResult | null>(null);
  const [status, setStatus] = useState<WhatIfStatus>('idle');
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async () => {
    if (!gridId) {
      setStatus('failed');
      setError('No grid loaded.');
      return;
    }
    setStatus('running');
    setError(null);
    try {
      if (dirty) await saveGrid();
      const request: Record<string, number> = {};
      if (values.solar !== null) request.solar_output_mw = values.solar;
      if (values.wind !== null) request.wind_output_mw = values.wind;
      if (values.battery !== null) request.battery_output_mw = values.battery;
      if (values.loadScale !== null) request.load_scale = values.loadScale;
      const powerResult = await analysisApi.runWhatIf(gridId, request);
      setResult(powerResult);
      setStatus('success');
    } catch (caught) {
      setError(describeError(caught));
      setStatus('failed');
    }
  }, [gridId, values, dirty, saveGrid]);

  const clear = useCallback(() => {
    setValues(EMPTY_VALUES);
    setResult(null);
    setStatus('idle');
    setError(null);
  }, []);

  const setValue = useCallback((key: keyof WhatIfValues, value: number | null) => {
    setValues((prev) => ({ ...prev, [key]: value }));
  }, []);

  const active =
    values.solar !== null ||
    values.wind !== null ||
    values.battery !== null ||
    values.loadScale !== null;

  const value = useMemo<WhatIfContextValue>(
    () => ({ active, values, result, status, error, setValue, run, clear }),
    [active, values, result, status, error, setValue, run, clear],
  );

  return <WhatIfContext.Provider value={value}>{children}</WhatIfContext.Provider>;
}

export function useWhatIf(): WhatIfContextValue {
  const ctx = useContext(WhatIfContext);
  if (!ctx) throw new Error('useWhatIf must be used inside WhatIfProvider');
  return ctx;
}
