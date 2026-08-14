import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { scenarioApi } from '../api/scenario';
import {
  addBus as editAddBus,
  addGenerator as editAddGenerator,
  addLine as editAddLine,
  addLoad as editAddLoad,
  copyGrid,
  removeBus as editRemoveBus,
  removeGenerator as editRemoveGenerator,
  removeLine as editRemoveLine,
  removeLoad as editRemoveLoad,
  updateBus as editUpdateBus,
  updateGenerator as editUpdateGenerator,
  updateLine as editUpdateLine,
  updateLoad as editUpdateLoad,
} from '../lib/gridEdit';
import { describeError } from '../lib/errors';
import type {
  GridModel,
  PowerFlowResult,
  Scenario,
  ScenarioSummary,
} from '../types';
import type { GridEditor } from './GridContext';
import { useGrid } from './GridContext';

type ScenarioRunState = 'idle' | 'running' | 'success' | 'failed' | 'error';

interface ScenarioContextValue {
  scenarios: ScenarioSummary[];
  activeScenario: Scenario | null;
  draft: GridModel | null;
  inScenarioMode: boolean;
  results: Record<string, PowerFlowResult>;
  runStates: Record<string, ScenarioRunState>;
  runErrors: Record<string, string>;
  scenarioError: string | null;
  refresh: () => Promise<void>;
  editScenario: (id: string) => Promise<void>;
  createScenario: (name: string) => Promise<void>;
  duplicateScenario: (id: string) => Promise<void>;
  deleteScenario: (id: string) => Promise<void>;
  saveDraft: () => Promise<void>;
  exitScenarioMode: () => void;
  runScenario: (id: string) => Promise<void>;
  draftEditor: GridEditor | null;
}

const ScenarioContext = createContext<ScenarioContextValue | null>(null);

export function ScenarioProvider({ children }: { children: ReactNode }) {
  const { gridId, grid: baseGrid } = useGrid();
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [fullScenarios, setFullScenarios] = useState<Record<string, Scenario>>({});
  const [activeScenario, setActiveScenario] = useState<Scenario | null>(null);
  const [draft, setDraft] = useState<GridModel | null>(null);
  const [results, setResults] = useState<Record<string, PowerFlowResult>>({});
  const [runStates, setRunStates] = useState<Record<string, ScenarioRunState>>({});
  const [runErrors, setRunErrors] = useState<Record<string, string>>({});
  const [scenarioError, setScenarioError] = useState<string | null>(null);

  const inScenarioMode = draft !== null && activeScenario !== null;

  const refresh = useCallback(async () => {
    if (!gridId) return;
    try {
      const list = await scenarioApi.list(gridId);
      setScenarios(list);
    } catch (error) {
      setScenarioError(describeError(error));
    }
  }, [gridId]);

  const editScenario = useCallback(
    async (id: string) => {
      if (!gridId) return;
      try {
        let scenario = fullScenarios[id];
        if (!scenario) {
          scenario = await scenarioApi.get(gridId, id);
          setFullScenarios((prev) => ({ ...prev, [id]: scenario }));
        }
        setActiveScenario(scenario);
        setDraft(copyGrid(scenario.grid));
      } catch (error) {
        setScenarioError(describeError(error));
      }
    },
    [gridId, fullScenarios],
  );

  const createScenario = useCallback(
    async (name: string) => {
      if (!gridId || !baseGrid) return;
      try {
        const created = await scenarioApi.create(gridId, name, copyGrid(baseGrid));
        setFullScenarios((prev) => ({ ...prev, [created.id]: created }));
        await refresh();
      } catch (error) {
        setScenarioError(describeError(error));
      }
    },
    [gridId, baseGrid, refresh],
  );

  const duplicateScenario = useCallback(
    async (id: string) => {
      if (!gridId) return;
      try {
        let scenario = fullScenarios[id];
        if (!scenario) {
          scenario = await scenarioApi.get(gridId, id);
          setFullScenarios((prev) => ({ ...prev, [id]: scenario }));
        }
        const created = await scenarioApi.create(
          gridId,
          `${scenario.name} copy`,
          copyGrid(scenario.grid),
        );
        setFullScenarios((prev) => ({ ...prev, [created.id]: created }));
        await refresh();
      } catch (error) {
        setScenarioError(describeError(error));
      }
    },
    [gridId, fullScenarios, refresh],
  );

  const deleteScenario = useCallback(
    async (id: string) => {
      if (!gridId) return;
      try {
        await scenarioApi.remove(gridId, id);
        setFullScenarios((prev) => {
          const next = { ...prev };
          delete next[id];
          return next;
        });
        setResults((prev) => {
          const next = { ...prev };
          delete next[id];
          return next;
        });
        setRunStates((prev) => {
          const next = { ...prev };
          delete next[id];
          return next;
        });
        if (activeScenario?.id === id) {
          setActiveScenario(null);
          setDraft(null);
        }
        await refresh();
      } catch (error) {
        setScenarioError(describeError(error));
      }
    },
    [gridId, activeScenario?.id, refresh],
  );

  const saveDraft = useCallback(async () => {
    if (!gridId || !activeScenario || !draft) return;
    try {
      const saved = await scenarioApi.create(
        gridId,
        draft.name,
        draft,
        activeScenario.id,
      );
      setActiveScenario(saved);
      setFullScenarios((prev) => ({ ...prev, [saved.id]: saved }));
      await refresh();
    } catch (error) {
      setScenarioError(describeError(error));
    }
  }, [gridId, activeScenario, draft, refresh]);

  const exitScenarioMode = useCallback(() => {
    setActiveScenario(null);
    setDraft(null);
  }, []);

  const runScenario = useCallback(
    async (id: string) => {
      if (!gridId) return;
      setRunStates((prev) => ({ ...prev, [id]: 'running' }));
      setRunErrors((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      try {
        const result = await scenarioApi.analyze(gridId, id);
        setResults((prev) => ({ ...prev, [id]: result }));
        setRunStates((prev) => ({
          ...prev,
          [id]: result.converged ? 'success' : 'failed',
        }));
      } catch (error) {
        setRunStates((prev) => ({ ...prev, [id]: 'error' }));
        setRunErrors((prev) => ({ ...prev, [id]: describeError(error) }));
      }
    },
    [gridId],
  );

  const draftEditor = useMemo<GridEditor | null>(() => {
    if (!inScenarioMode || !draft) return null;
    const g = draft;
    const applyDraft = (next: GridModel) => setDraft(next);
    return {
      addBus: () => {
        const result = editAddBus(g);
        applyDraft(result.grid);
        return result.id;
      },
      updateBus: (id, patch) => applyDraft(editUpdateBus(g, id, patch)),
      removeBus: (id) => applyDraft(editRemoveBus(g, id)),
      addLine: (from, to) => {
        const result = editAddLine(g, from, to);
        applyDraft(result.grid);
        return result.id;
      },
      updateLine: (id, patch) => applyDraft(editUpdateLine(g, id, patch)),
      removeLine: (id) => applyDraft(editRemoveLine(g, id)),
      addGenerator: (busId, type) => {
        const result = editAddGenerator(g, busId, type);
        applyDraft(result.grid);
        return result.id;
      },
      updateGenerator: (id, patch) => applyDraft(editUpdateGenerator(g, id, patch)),
      removeGenerator: (id) => applyDraft(editRemoveGenerator(g, id)),
      addLoad: (busId) => {
        const result = editAddLoad(g, busId);
        applyDraft(result.grid);
        return result.id;
      },
      updateLoad: (id, patch) => applyDraft(editUpdateLoad(g, id, patch)),
      removeLoad: (id) => applyDraft(editRemoveLoad(g, id)),
      moveBus: (_id, _x, _y) => {
        // scenario drafts keep the base layout
      },
    };
  }, [inScenarioMode, draft]);

  const value = useMemo<ScenarioContextValue>(
    () => ({
      scenarios,
      activeScenario,
      draft,
      inScenarioMode,
      results,
      runStates,
      runErrors,
      scenarioError,
      refresh,
      editScenario,
      createScenario,
      duplicateScenario,
      deleteScenario,
      saveDraft,
      exitScenarioMode,
      runScenario,
      draftEditor,
    }),
    [
      scenarios,
      activeScenario,
      draft,
      inScenarioMode,
      results,
      runStates,
      runErrors,
      scenarioError,
      refresh,
      editScenario,
      createScenario,
      duplicateScenario,
      deleteScenario,
      saveDraft,
      exitScenarioMode,
      runScenario,
      draftEditor,
    ],
  );

  return <ScenarioContext.Provider value={value}>{children}</ScenarioContext.Provider>;
}

export function useScenario(): ScenarioContextValue {
  const ctx = useContext(ScenarioContext);
  if (!ctx) throw new Error('useScenario must be used inside ScenarioProvider');
  return ctx;
}
