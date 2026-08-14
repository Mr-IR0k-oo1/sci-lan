import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { demoGrids, gridApi } from '../api/grid';
import {
  addBus as editAddBus,
  addGenerator as editAddGenerator,
  addLine as editAddLine,
  addLoad as editAddLoad,
  removeBus as editRemoveBus,
  removeGenerator as editRemoveGenerator,
  removeLine as editRemoveLine,
  removeLoad as editRemoveLoad,
  updateBus as editUpdateBus,
  updateGenerator as editUpdateGenerator,
  updateLine as editUpdateLine,
  updateLoad as editUpdateLoad,
} from '../lib/gridEdit';
import { ensurePositions, type Point } from '../lib/positions';
import type {
  Bus,
  Generator,
  GeneratorType,
  GridModel,
  Load,
  TransmissionLine,
} from '../types';

export interface GridEditor {
  addBus: () => string | undefined;
  updateBus: (id: string, patch: Partial<Bus>) => void;
  removeBus: (id: string) => void;
  addLine: (from: string, to: string) => string | null;
  updateLine: (id: string, patch: Partial<TransmissionLine>) => void;
  removeLine: (id: string) => void;
  addGenerator: (busId: string, type: GeneratorType) => string | undefined;
  updateGenerator: (id: string, patch: Partial<Generator>) => void;
  removeGenerator: (id: string) => void;
  addLoad: (busId: string) => string | undefined;
  updateLoad: (id: string, patch: Partial<Load>) => void;
  removeLoad: (id: string) => void;
  moveBus: (id: string, x: number, y: number) => void;
}

interface GridContextValue {
  grid: GridModel | null;
  gridId: string | null;
  dirty: boolean;
  loading: boolean;
  saving: boolean;
  loadError: string | null;
  positions: Record<string, Point>;
  availableGridIds: string[];
  refreshAvailable: () => Promise<void>;
  loadGrid: (id: string) => Promise<void>;
  createNewGrid: () => Promise<void>;
  saveGrid: () => Promise<GridModel | null>;
  setGridName: (name: string) => void;
  setBaseMva: (mva: number) => void;
  moveBus: (id: string, x: number, y: number) => void;
  editor: GridEditor;
}

const GridContext = createContext<GridContextValue | null>(null);

export function GridProvider({ children }: { children: ReactNode }) {
  const [grid, setGrid] = useState<GridModel | null>(null);
  const [gridId, setGridId] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [positions, setPositions] = useState<Record<string, Point>>({});
  const [availableGridIds, setAvailableGridIds] = useState<string[]>([]);

  const markDirty = useCallback(() => setDirty(true), []);

  const setGridWithPositions = useCallback(
    (next: GridModel) => {
      setGrid(next);
      setPositions((prev) => ensurePositions(next.buses, prev));
    },
    [],
  );

  const loadGrid = useCallback(async (id: string) => {
    setLoading(true);
    setLoadError(null);
    try {
      const loaded = await gridApi.get(id);
      setGrid(loaded);
      setGridId(loaded.grid_id);
      setPositions({});
      setPositions((prev) => ensurePositions(loaded.buses, prev));
      setDirty(false);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'Failed to load grid.');
    } finally {
      setLoading(false);
    }
  }, []);

  const createNewGrid = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const busId = 'B1';
      const fresh: GridModel = {
        grid_id: '',
        name: 'New Grid',
        base_mva: 100,
        buses: [
          {
            id: busId,
            name: 'Slack Bus',
            type: 'SLACK',
            base_voltage: 138,
            voltage_magnitude: 1.0,
            voltage_angle: 0.0,
          },
        ],
        lines: [],
        generators: [
          {
            id: 'G1',
            name: 'Slack Generator',
            bus_id: busId,
            type: 'CONVENTIONAL',
            active_power: 0,
            reactive_power: 0,
            active_power_min: 0,
            active_power_max: 300,
            reactive_power_min: -100,
            reactive_power_max: 100,
            capacity_mwh: 0,
          },
        ],
        loads: [],
      };
      const created = await gridApi.create(fresh);
      setGrid(created);
      setGridId(created.grid_id);
      setPositions({});
      setPositions((prev) => ensurePositions(created.buses, prev));
      setDirty(false);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'Failed to create grid.');
    } finally {
      setLoading(false);
    }
  }, []);

  const saveGrid = useCallback(async (): Promise<GridModel | null> => {
    if (!grid || !gridId) return null;
    setSaving(true);
    try {
      const saved = await gridApi.update(gridId, grid);
      setGrid(saved);
      setGridId(saved.grid_id);
      setDirty(false);
      return saved;
    } finally {
      setSaving(false);
    }
  }, [grid, gridId]);

  const applyUpdate = useCallback(
    (next: GridModel) => {
      setGridWithPositions(next);
      markDirty();
    },
    [setGridWithPositions, markDirty],
  );

  const editor = useMemo<GridEditor>(
    () => ({
      addBus: () => {
        if (!grid) return undefined;
        const result = editAddBus(grid);
        applyUpdate(result.grid);
        return result.id;
      },
      updateBus: (id, patch) => {
        if (grid) applyUpdate(editUpdateBus(grid, id, patch));
      },
      removeBus: (id) => {
        if (grid) applyUpdate(editRemoveBus(grid, id));
      },
      addLine: (from, to) => {
        if (!grid) return null;
        const result = editAddLine(grid, from, to);
        applyUpdate(result.grid);
        return result.id;
      },
      updateLine: (id, patch) => {
        if (grid) applyUpdate(editUpdateLine(grid, id, patch));
      },
      removeLine: (id) => {
        if (grid) applyUpdate(editRemoveLine(grid, id));
      },
      addGenerator: (busId, type) => {
        if (!grid) return undefined;
        const result = editAddGenerator(grid, busId, type);
        applyUpdate(result.grid);
        return result.id;
      },
      updateGenerator: (id, patch) => {
        if (grid) applyUpdate(editUpdateGenerator(grid, id, patch));
      },
      removeGenerator: (id) => {
        if (grid) applyUpdate(editRemoveGenerator(grid, id));
      },
      addLoad: (busId) => {
        if (!grid) return undefined;
        const result = editAddLoad(grid, busId);
        applyUpdate(result.grid);
        return result.id;
      },
      updateLoad: (id, patch) => {
        if (grid) applyUpdate(editUpdateLoad(grid, id, patch));
      },
      removeLoad: (id) => {
        if (grid) applyUpdate(editRemoveLoad(grid, id));
      },
      moveBus: (id, x, y) => {
        setPositions((prev) => ({ ...prev, [id]: { x, y } }));
      },
    }),
    [grid, applyUpdate],
  );

  const refreshAvailable = useCallback(async () => {
    try {
      const grids = await demoGrids.list();
      setAvailableGridIds(grids.map((g) => g.grid_id));
    } catch {
      setAvailableGridIds([]);
    }
  }, []);

  const value = useMemo<GridContextValue>(
    () => ({
      grid,
      gridId,
      dirty,
      loading,
      saving,
      loadError,
      positions,
      availableGridIds,
      refreshAvailable,
      loadGrid,
      createNewGrid,
      saveGrid,
      setGridName: (name) => {
        if (grid) applyUpdate({ ...grid, name });
      },
      setBaseMva: (mva) => {
        if (grid) applyUpdate({ ...grid, base_mva: mva });
      },
      moveBus: editor.moveBus,
      editor,
    }),
    [
      grid,
      gridId,
      dirty,
      loading,
      saving,
      loadError,
      positions,
      availableGridIds,
      refreshAvailable,
      loadGrid,
      createNewGrid,
      saveGrid,
      editor,
      applyUpdate,
    ],
  );

  return <GridContext.Provider value={value}>{children}</GridContext.Provider>;
}

export function useGrid(): GridContextValue {
  const ctx = useContext(GridContext);
  if (!ctx) throw new Error('useGrid must be used inside GridProvider');
  return ctx;
}
