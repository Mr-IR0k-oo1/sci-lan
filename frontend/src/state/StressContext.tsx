import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { stressApi } from '../api/stress';
import { describeError } from '../lib/errors';
import type {
  AnalysisRecord,
  MitigationTestResult,
} from '../types';
import { useGrid } from './GridContext';

export type StressStatus = 'idle' | 'running' | 'success' | 'failed' | 'error';

interface StressContextValue {
  status: StressStatus;
  record: AnalysisRecord | null;
  error: string | null;
  runStress: () => Promise<void>;
  runMitigationTests: (candidateIds?: string[]) => Promise<void>;
  clear: () => void;
}

const StressContext = createContext<StressContextValue | null>(null);

export function StressProvider({ children }: { children: ReactNode }) {
  const { gridId, dirty, saveGrid } = useGrid();
  const [status, setStatus] = useState<StressStatus>('idle');
  const [record, setRecord] = useState<AnalysisRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runStress = useCallback(async () => {
    if (!gridId) {
      setStatus('error');
      setError('No grid loaded. Create or open a grid first.');
      return;
    }
    setError(null);
    setStatus('running');
    try {
      if (dirty) await saveGrid();
      const analysis = await stressApi.runStress(gridId);
      setRecord(analysis);
      setStatus('success');
    } catch (caught) {
      setError(describeError(caught));
      setStatus('error');
    }
  }, [gridId, dirty, saveGrid]);

  const runMitigationTests = useCallback(
    async (candidateIds?: string[]) => {
      if (!record) return;
      setError(null);
      const targets = candidateIds ?? record.mitigation_candidates.map((c) => c.id);
      const results: MitigationTestResult[] = [];
      for (const id of targets) {
        const tested = await stressApi.runMitigationTests(record.id, id);
        results.push(...tested);
      }
      setRecord((prev) => (prev ? { ...prev, mitigation_tests: results } : prev));
    },
    [record],
  );

  const clear = useCallback(() => {
    setRecord(null);
    setStatus('idle');
    setError(null);
  }, []);

  const value = useMemo<StressContextValue>(
    () => ({ status, record, error, runStress, runMitigationTests, clear }),
    [status, record, error, runStress, runMitigationTests, clear],
  );

  return <StressContext.Provider value={value}>{children}</StressContext.Provider>;
}

export function useStress(): StressContextValue {
  const ctx = useContext(StressContext);
  if (!ctx) throw new Error('useStress must be used inside StressProvider');
  return ctx;
}
