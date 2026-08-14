import { describe, expect, it } from 'vitest';
import { issueTarget } from '../src/lib/issues';
import type { ValidationIssue } from '../src/types';
import { sampleGrid } from './fixtures';

describe('issueTarget', () => {
  it('maps a line issue to the line component', () => {
    const issue: ValidationIssue = {
      code: 'invalid_line_parameters',
      message: "Line 'L1' has zero reactance.",
      location: 'lines',
    };
    expect(issueTarget(issue, sampleGrid)).toEqual({ kind: 'line', id: 'L1' });
  });

  it('returns null when the mentioned id does not exist', () => {
    const issue: ValidationIssue = {
      code: 'invalid_line_bus_reference',
      message: "Line 'L9' references unknown to_bus 'B7'.",
      location: 'lines',
    };
    expect(issueTarget(issue, sampleGrid)).toBeNull();
  });

  it('falls back to a bus for missing-slack issues', () => {
    const issue: ValidationIssue = {
      code: 'missing_slack',
      message: 'Grid must have exactly one slack bus.',
      location: 'buses',
    };
    expect(issueTarget(issue, sampleGrid)?.kind).toBe('bus');
  });

  it('returns null for issues with no selectable component', () => {
    const issue: ValidationIssue = {
      code: 'no_buses',
      message: 'Grid must contain at least one bus.',
      location: 'buses',
    };
    expect(issueTarget(issue, sampleGrid)).toBeNull();
  });
});
