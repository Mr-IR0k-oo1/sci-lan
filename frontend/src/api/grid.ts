import { get, post, put } from './client';
import type { GridModel, ValidationResponse } from '../types';

export const gridApi = {
  create(grid: GridModel): Promise<GridModel> {
    return post<GridModel>('/grids', grid);
  },

  get(gridId: string): Promise<GridModel> {
    return get<GridModel>(`/grids/${gridId}`);
  },

  update(gridId: string, grid: GridModel): Promise<GridModel> {
    return put<GridModel>(`/grids/${gridId}`, grid);
  },

  validate(gridId: string): Promise<ValidationResponse> {
    return post<ValidationResponse>(`/grids/${gridId}/validate`, {});
  },
};

export const demoGrids = {
  list(): Promise<GridModel[]> {
    return get<GridModel[]>('/grids');
  },
};
