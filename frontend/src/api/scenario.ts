import { del, get, post } from './client';
import type {
  GridModel,
  PowerFlowRequest,
  PowerFlowResult,
  Scenario,
  ScenarioSummary,
} from '../types';

export const scenarioApi = {
  list(gridId: string): Promise<ScenarioSummary[]> {
    return get<ScenarioSummary[]>(`/grids/${gridId}/scenarios`);
  },

  get(gridId: string, scenarioId: string): Promise<Scenario> {
    return get<Scenario>(`/grids/${gridId}/scenarios/${scenarioId}`);
  },

  create(gridId: string, name: string, grid: GridModel, id?: string): Promise<Scenario> {
    const body: Record<string, unknown> = { name, grid };
    if (id) body.id = id;
    return post<Scenario>(`/grids/${gridId}/scenarios`, body);
  },

  analyze(gridId: string, scenarioId: string, request?: PowerFlowRequest): Promise<PowerFlowResult> {
    return post<PowerFlowResult>(`/grids/${gridId}/scenarios/${scenarioId}/analyze`, request ?? {});
  },

  remove(gridId: string, scenarioId: string): Promise<void> {
    return del<void>(`/grids/${gridId}/scenarios/${scenarioId}`);
  },
};
