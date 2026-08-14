import type { SeverityLevel, StressLevel } from '../types';

export const STRESS_LEVEL_LABELS: Record<StressLevel, string> = {
  LOW: 'Low',
  MODERATE: 'Moderate',
  HIGH: 'High',
  CRITICAL: 'Critical',
};

export const SEVERITY_LABELS: Record<SeverityLevel, string> = {
  NORMAL: 'Normal',
  WARNING: 'Warning',
  CRITICAL: 'Critical',
};

export function stressLevelClass(level: StressLevel): string {
  switch (level) {
    case 'CRITICAL':
      return 'status-bad';
    case 'HIGH':
      return 'status-bad';
    case 'MODERATE':
      return 'status-warn';
    case 'LOW':
      return 'status-ok';
    default:
      return 'status-idle';
  }
}

export function severityClass(severity: SeverityLevel): string {
  switch (severity) {
    case 'CRITICAL':
      return 'status-bad';
    case 'WARNING':
      return 'status-warn';
    case 'NORMAL':
      return 'status-ok';
    default:
      return 'status-idle';
  }
}

export function impactLevelLabel(level: string): string {
  switch (level) {
    case 'POSITIVE':
      return 'Positive';
    case 'NEGATIVE':
      return 'Negative';
    case 'HIGH_RISK':
      return 'High risk';
    default:
      return 'Neutral';
  }
}

export function impactLevelClass(level: string): string {
  switch (level) {
    case 'POSITIVE':
      return 'status-ok';
    case 'NEGATIVE':
      return 'status-warn';
    case 'HIGH_RISK':
      return 'status-bad';
    default:
      return 'status-idle';
  }
}
