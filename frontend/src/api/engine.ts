import { get } from './client';
import type { EngineRegistry } from '../types';

export const engineApi = {
  status(): Promise<EngineRegistry> {
    return get<EngineRegistry>('/engines');
  },
};
