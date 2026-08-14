import type { GeneratorType } from '../../types';
import type { ComponentSelection } from '../../types';
import type { GridEditor } from '../../state/GridContext';
import { Section } from '../ui';
import { LineIcon, PlusIcon } from '../icons';
import { GENERATOR_TYPE_LABELS } from '../../lib/labels';
import type { GridModel } from '../../types';

interface ComponentPaletteProps {
  grid: GridModel;
  editor: GridEditor;
  selected: ComponentSelection | null;
  lineToolActive: boolean;
  setLineToolActive: (active: boolean) => void;
  onSelect: (selection: ComponentSelection | null) => void;
}

const GENERATOR_TYPES: GeneratorType[] = ['CONVENTIONAL', 'SOLAR', 'WIND', 'STORAGE'];

export function ComponentPalette({
  grid,
  editor,
  selected,
  lineToolActive,
  setLineToolActive,
  onSelect,
}: ComponentPaletteProps) {
  const targetBusId = selected?.kind === 'bus' ? selected.id : null;

  const addGenerator = (type: GeneratorType) => {
    if (!targetBusId) return;
    const id = editor.addGenerator(targetBusId, type);
    if (id) onSelect({ kind: 'generator', id });
  };

  const addLoad = () => {
    if (!targetBusId) return;
    const id = editor.addLoad(targetBusId);
    if (id) onSelect({ kind: 'load', id });
  };

  return (
    <Section title="Components">
      <div className="palette">
        <div className="palette-group">
          <h4>Add</h4>
          <button
            type="button"
            className="palette-item"
            onClick={() => {
              const id = editor.addBus();
              if (id) onSelect({ kind: 'bus', id });
            }}
          >
            <PlusIcon />
            <span>Bus</span>
          </button>
          <button
            type="button"
            className={`palette-item${lineToolActive ? ' palette-item-active' : ''}`}
            onClick={() => {
              setLineToolActive(!lineToolActive);
              if (!lineToolActive) onSelect(null);
            }}
          >
            <LineIcon />
            <span>Line (click two buses)</span>
          </button>
        </div>

        <div className="palette-group">
          <h4>Generators</h4>
          {!targetBusId ? (
            <p className="panel-hint">Select a bus first, then add a generator.</p>
          ) : null}
          {GENERATOR_TYPES.map((type) => (
            <button
              key={type}
              type="button"
              className="palette-item"
              disabled={!targetBusId}
              onClick={() => addGenerator(type)}
            >
              <span className="glyph glyph-generator" aria-hidden="true" />
              <span>{GENERATOR_TYPE_LABELS[type]}</span>
            </button>
          ))}
        </div>

        <div className="palette-group">
          <h4>Load</h4>
          <button type="button" className="palette-item" disabled={!targetBusId} onClick={addLoad}>
            <span className="glyph glyph-load" aria-hidden="true" />
            <span>Add load</span>
          </button>
        </div>

        {grid.buses.length === 0 ? (
          <p className="panel-hint">Start by adding a bus.</p>
        ) : null}
      </div>
    </Section>
  );
}
