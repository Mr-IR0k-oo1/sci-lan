import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { analysisApi } from '../api/analysis';
import { gridApi } from '../api/grid';
import { describeError } from '../lib/errors';
import type { PowerFlowResult, ValidationIssue } from '../types';
import { useGrid } from './GridContext';

export type AnalysisStatus = 'idle' | 'validating' | 'running' | 'success' | 'failed' | 'error' | 'outdated';

interface AnalysisContextValue {
  status: AnalysisStatus;
  result: PowerFlowResult | null;
  validationIssues: ValidationIssue[];
  error: string | null;
  engine: string;
  setEngine: (engine: string) => void;
  runAnalysis: () => Promise<void>;
}

const AnalysisContext = createContext<AnalysisContextValue | null>(null);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const { gridId, dirty, saveGrid } = useGrid();
  const [status, setStatus] = useState<AnalysisStatus>('idle');
  const [result, setResult] = useState<PowerFlowResult | null>(null);
  const [validationIssues, setValidationIssues] = useState<ValidationIssue[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [engine, setEngine] = useState<string>('auto');

  // If the grid becomes dirty after a successful analysis, mark it as outdated
  useEffect(() => {
    if (dirty && (status === 'success' || status === 'failed')) {
      setStatus('outdated');
    }
  }, [dirty, status]);

  const runAnalysis = useCallback(async () => {
    if (!gridId) {
      setStatus('error');
      setError('No grid loaded. Create or open a grid first.');
      return;
    }
    setError(null);
    setStatus('validating');
    if (dirty) {
      const saved = await saveGrid();
      if (!saved) {
        setStatus('error');
        setError('Could not save the grid before analysis.');
        return;
      }
    }
    const validation = await gridApi.validate(gridId);
    if (!validation.valid) {
      setValidationIssues(validation.errors);
      setResult(null);
      setStatus('failed');
      return;
    }
    setValidationIssues([]);
    setStatus('running');
    try {
      const powerResult = await analysisApi.runPowerFlow(gridId, { engine });
      setResult(powerResult);
      setStatus(powerResult.converged ? 'success' : 'failed');
      if (!powerResult.converged) {
        setError('Power flow did not converge.');
      }
    } catch (caught) {
      setError(describeError(caught));
      setStatus('error');
    }
  }, [gridId, dirty, saveGrid, engine]);

  const value = useMemo<AnalysisContextValue>(
    () => ({ status, result, validationIssues, error, engine, setEngine, runAnalysis }),
    [status, result, validationIssues, error, engine, setEngine, runAnalysis],
  );

  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>;
}

export function useAnalysis(): AnalysisContextValue {
  const ctx = useContext(AnalysisContext);
  if (!ctx) throw new Error('useAnalysis must be used inside AnalysisProvider');
  return ctx;
}
