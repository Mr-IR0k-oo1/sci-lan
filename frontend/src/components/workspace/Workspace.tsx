import { useEffect, useMemo, useRef } from 'react';
import { circlePosition, type Point } from '../../lib/positions';
import { GridProvider, useGrid } from '../../state/GridContext';
import { AnalysisProvider, useAnalysis } from '../../state/AnalysisContext';
import { ScenarioProvider, useScenario } from '../../state/ScenarioContext';
import { WhatIfProvider } from '../../state/WhatIfContext';
import { SelectionProvider, useSelection } from '../../state/SelectionContext';
import { TopBar } from './TopBar';
import { ComponentPalette } from './ComponentPalette';
import { PropertiesPanel } from './PropertiesPanel';
import { ValidationPanel } from './ValidationPanel';
import { ScenarioPanel } from './ScenarioPanel';
import { WhatIfPanel } from './WhatIfPanel';
import { AnalysisResultsPanel } from './AnalysisResultsPanel';
import { GridCanvas } from './GridCanvas';

function WorkspaceInner() {
  const gridState = useGrid();
  const analysis = useAnalysis();
  const scenario = useScenario();
  const selection = useSelection();
  const {
    selected,
    select: onSelect,
    lineToolActive,
    setLineToolActive,
    lineFrom,
    setLineFrom,
  } = selection;

  const autoLoaded = useRef(false);

  useEffect(() => {
    void gridState.refreshAvailable();
  }, [gridState.refreshAvailable]);

  useEffect(() => {
    if (autoLoaded.current) return;
    if (gridState.availableGridIds.length > 0) {
      autoLoaded.current = true;
      void gridState.loadGrid(gridState.availableGridIds[0]);
    }
  }, [gridState.availableGridIds, gridState.loadGrid]);

  const inScenarioMode = scenario.inScenarioMode;
  const activeGrid = inScenarioMode ? scenario.draft : gridState.grid;
  const activeEditor = inScenarioMode ? scenario.draftEditor : gridState.editor;

  const canvasResult =
    inScenarioMode ? null : analysis.result;

  const canvasPositions = useMemo(() => {
    const next: Record<string, Point> = {};
    if (activeGrid) {
      activeGrid.buses.forEach((bus, index) => {
        next[bus.id] = gridState.positions[bus.id] ?? circlePosition(index, activeGrid.buses.length);
      });
    }
    return next;
  }, [activeGrid, gridState.positions]);

  const onSave = inScenarioMode
    ? () => void scenario.saveDraft()
    : () => void gridState.saveGrid();
  const saveLabel = inScenarioMode ? 'Save Scenario' : 'Save Grid';

  return (
    <div className="workspace">
      <TopBar />

      <div className="workspace-main">
        <aside className="left-panel">
          {activeGrid && activeEditor ? (
            <ComponentPalette
              grid={activeGrid}
              editor={activeEditor}
              selected={selected}
              lineToolActive={lineToolActive}
              setLineToolActive={setLineToolActive}
              onSelect={onSelect}
            />
          ) : null}
          <ScenarioPanel />
          <WhatIfPanel />
        </aside>

        <main className="canvas-area">
          {inScenarioMode ? (
            <div className="scenario-mode-banner" data-testid="scenario-banner">
              <span>
                <strong>SCENARIO MODE</strong> — editing {scenario.activeScenario?.name}. The base
                grid is unchanged until you save the scenario.
              </span>
            </div>
          ) : null}

          {activeGrid && activeEditor ? (
            <GridCanvas
              grid={activeGrid}
              positions={canvasPositions}
              editor={activeEditor}
              result={canvasResult}
              selected={selected}
              onSelect={onSelect}
              lineToolActive={lineToolActive}
              lineFrom={lineFrom}
              setLineFrom={setLineFrom}
            />
          ) : (
            <div className="canvas-placeholder">
              <p className="panel-hint">
                No grid loaded. Create a new grid or select one from the top bar.
              </p>
            </div>
          )}
        </main>

        <aside className="right-panel">
          {activeGrid && activeEditor ? (
            <PropertiesPanel
              grid={activeGrid}
              selected={selected}
              editor={activeEditor}
              onSelect={onSelect}
              onSave={onSave}
              saving={inScenarioMode ? false : gridState.saving}
              saveLabel={saveLabel}
              onNameChange={inScenarioMode ? () => undefined : gridState.setGridName}
              onBaseMvaChange={inScenarioMode ? () => undefined : gridState.setBaseMva}
              allowGridSave={!inScenarioMode}
            />
          ) : null}
          <ValidationPanel grid={gridState.grid} issues={analysis.validationIssues} onSelect={onSelect} />
        </aside>
      </div>

      <AnalysisResultsPanel result={analysis.result} status={analysis.status} error={analysis.error} />
    </div>
  );
}

export function Workspace() {
  return (
    <SelectionProvider>
      <GridProvider>
        <ScenarioProvider>
          <AnalysisProvider>
            <WhatIfProvider>
              <WorkspaceInner />
            </WhatIfProvider>
          </AnalysisProvider>
        </ScenarioProvider>
      </GridProvider>
    </SelectionProvider>
  );
}

export default Workspace;
