import { get, post } from './client';
import type { EngineRegistry, PowerFlowRequest, PowerFlowResult, WhatIfRequest } from '../types';

export const analysisApi = {
  runPowerFlow(gridId: string, request?: PowerFlowRequest): Promise<PowerFlowResult> {
    return post<PowerFlowResult>(`/grids/${gridId}/analyze/power-flow`, request ?? {});
  },

  runWhatIf(gridId: string, request: WhatIfRequest): Promise<PowerFlowResult> {
    return post<PowerFlowResult>(`/grids/${gridId}/what-if`, request);
  },

  getEngines(): Promise<EngineRegistry> {
    return get<EngineRegistry>('/engines');
  },
};
