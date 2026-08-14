import type { BusStatus, LineStatus } from '../types';

export function formatNumber(value: number, digits = 2): string {
  if (!Number.isFinite(value)) return '—';
  return value.toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  });
}

export function formatPercent(value: number, digits = 1): string {
  if (!Number.isFinite(value)) return '—';
  return `${value.toFixed(digits)}%`;
}

export function formatSigned(value: number, digits = 2): string {
  const sign = value > 0 ? '+' : '';
  return `${sign}${formatNumber(value, digits)}`;
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export const BUS_STATUS_LABELS: Record<BusStatus, string> = {
  NORMAL: 'Normal',
  WARNING: 'Warning',
  CRITICAL: 'Critical',
};

export const LINE_STATUS_LABELS: Record<LineStatus, string> = {
  NORMAL: 'Normal',
  WARNING: 'Near limit',
  OVERLOADED: 'Overloaded',
};

export function busStatusClass(status: BusStatus): string {
  switch (status) {
    case 'NORMAL':
      return 'status-ok';
    case 'WARNING':
      return 'status-warn';
    case 'CRITICAL':
      return 'status-bad';
    default:
      return 'status-idle';
  }
}

export function lineStatusClass(status: LineStatus): string {
  switch (status) {
    case 'NORMAL':
      return 'status-ok';
    case 'WARNING':
      return 'status-warn';
    case 'OVERLOADED':
      return 'status-bad';
    default:
      return 'status-idle';
  }
}

export function voltageClass(voltage: number): string {
  if (voltage > 1.1 || voltage < 0.9) return 'status-bad';
  if (voltage > 1.05 || voltage < 0.95) return 'status-warn';
  return 'status-ok';
}
