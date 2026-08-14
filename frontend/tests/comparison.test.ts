import { describe, expect, it } from 'vitest';
import type { PowerFlowResult } from '../src/types';
import {
  buildLineComparison,
  buildMetricComparison,
  buildVoltageComparison,
} from '../src/lib/comparison';
import { sampleResult, whatIfResult } from './fixtures';

describe('comparison builders', () => {
  it('computes metrics with absolute and percentage change', () => {
    const rows = buildMetricComparison(sampleResult, whatIfResult);
    const renewable = rows.find((row) => row.metric === 'Renewable generation');
    const losses = rows.find((row) => row.metric === 'Total losses');
    expect(renewable).toMatchObject({ base: 0, scenario: 100, change: 100 });
    expect(renewable?.changePercent).toBeNull();
    expect(losses).toMatchObject({ base: 2.5, scenario: 3.1 });
    expect(losses?.changePercent).toBeCloseTo(24, 5);
  });

  it('shows a percentage when the base value is non-zero', () => {
    const rows = buildMetricComparison(sampleResult, whatIfResult);
    const generation = rows.find((row) => row.metric === 'Total generation');
    expect(generation?.change).toBeCloseTo(20, 5);
    expect(generation?.changePercent).toBeCloseTo(17.0213, 2);
  });

  it('returns an empty list when summaries are missing', () => {
    const noSummary: PowerFlowResult = { ...sampleResult, summary: null };
    expect(buildMetricComparison(noSummary, sampleResult)).toEqual([]);
  });

  it('builds voltage rows with a classification', () => {
    const rows = buildVoltageComparison(sampleResult, whatIfResult);
    expect(rows.length).toBeGreaterThan(0);
    const b1 = rows.find((row) => row.busId === 'B1');
    expect(b1).toBeDefined();
    expect(['improved', 'warning', 'violation', 'unchanged']).toContain(b1?.classification);
  });

  it('builds line rows and flags status transitions', () => {
    const scenario: PowerFlowResult = {
      ...whatIfResult,
      lines: whatIfResult.lines.map((line, index) =>
        index === 0 ? { ...line, loading_percentage: 112, status: 'OVERLOADED' as const } : line,
      ),
    };
    const rows = buildLineComparison(sampleResult, scenario);
    const l1 = rows.find((row) => row.lineId === 'L1');
    expect(l1?.baseLoading).toBe(11.6);
    expect(l1?.scenarioLoading).toBe(112);
    expect(l1?.scenarioStatus).toBe('OVERLOADED');
    expect(l1?.transition).toBe(true);
  });
});
