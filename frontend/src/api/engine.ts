import { get, post } from './client';
import type {
  CompareEnginesRequest,
  EngineComparisonResponse,
  EngineRegistry,
  ScilabStatus,
} from '../types';

export const engineApi = {
  status(): Promise<EngineRegistry> {
    return get<EngineRegistry>('/engines');
  },

  scilabStatus(): Promise<ScilabStatus> {
    return get<ScilabStatus>('/engines/scilab/status');
  },

  compare(request: CompareEnginesRequest): Promise<EngineComparisonResponse> {
    return post<EngineComparisonResponse>('/compare-engines', request);
  },
};
