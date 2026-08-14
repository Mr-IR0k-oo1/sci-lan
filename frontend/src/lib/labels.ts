import type { BusType, GeneratorType } from '../types';

export const BUS_TYPE_LABELS: Record<BusType, string> = {
  SLACK: 'Slack',
  PV: 'PV (regulated)',
  PQ: 'PQ (load)',
};

export const GENERATOR_TYPE_LABELS: Record<GeneratorType, string> = {
  CONVENTIONAL: 'Conventional',
  SOLAR: 'Solar',
  WIND: 'Wind',
  STORAGE: 'Battery',
};
