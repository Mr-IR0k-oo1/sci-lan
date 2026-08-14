import type { GeneratorType, GridModel } from '../../types';
import type { ComponentSelection } from '../../types';
import { NumberField, SelectField, TextField } from '../NumberField';
import { Button, Section } from '../ui';
import { BUS_TYPE_LABELS, GENERATOR_TYPE_LABELS } from '../../lib/labels';
import type { GridEditor } from '../../state/GridContext';

interface PropertiesPanelProps {
  grid: GridModel;
  selected: ComponentSelection | null;
  editor: GridEditor;
  onSelect: (selection: ComponentSelection | null) => void;
  onSave: () => void;
  saving: boolean;
  saveLabel: string;
  onNameChange: (name: string) => void;
  onBaseMvaChange: (mva: number) => void;
  allowGridSave: boolean;
}

export function PropertiesPanel({
  grid,
  selected,
  editor,
  onSelect,
  onSave,
  saving,
  saveLabel,
  onNameChange,
  onBaseMvaChange,
  allowGridSave,
}: PropertiesPanelProps) {
  if (!selected) {
    if (!allowGridSave) {
      return (
        <Section title="Grid">
          <p className="panel-hint">
            Scenario mode — select a component on the canvas to edit the scenario copy.
          </p>
        </Section>
      );
    }
    return (
      <Section title="Grid">
        <TextField label="Name" value={grid.name} onChange={onNameChange} />
        <NumberField
          label="Base power (MVA)"
          value={grid.base_mva}
          min={1}
          suffix="MVA"
          onChange={onBaseMvaChange}
        />
        <p className="panel-hint">Select a component on the canvas to edit it.</p>
        <Button onClick={onSave} disabled={saving}>
          {saveLabel}
        </Button>
      </Section>
    );
  }

  if (selected.kind === 'bus') {
    const bus = grid.buses.find((item) => item.id === selected.id);
    if (!bus) return null;
    return (
      <Section
        title={`Bus ${bus.id}`}
        action={
          <Button
            variant="danger"
            onClick={() => {
              editor.removeBus(bus.id);
              onSelect(null);
            }}
          >
            Delete
          </Button>
        }
      >
        <TextField label="Name" value={bus.name} onChange={(name) => editor.updateBus(bus.id, { name })} />
        <SelectField
          label="Type"
          value={bus.type}
          options={(Object.keys(BUS_TYPE_LABELS) as Array<keyof typeof BUS_TYPE_LABELS>).map(
            (type) => ({ value: type, label: BUS_TYPE_LABELS[type] }),
          )}
          onChange={(type) => editor.updateBus(bus.id, { type })}
        />
        <NumberField
          label="Base voltage (kV)"
          value={bus.base_voltage}
          min={0.1}
          suffix="kV"
          onChange={(base_voltage) => editor.updateBus(bus.id, { base_voltage })}
        />
        {bus.type === 'SLACK' || bus.type === 'PV' ? (
          <NumberField
            label="Voltage magnitude (pu)"
            value={bus.voltage_magnitude}
            min={0.7}
            max={1.3}
            step={0.01}
            suffix="pu"
            onChange={(voltage_magnitude) => editor.updateBus(bus.id, { voltage_magnitude })}
          />
        ) : null}
        {bus.type === 'SLACK' ? (
          <NumberField
            label="Voltage angle (°)"
            value={bus.voltage_angle}
            step={0.5}
            suffix="°"
            onChange={(voltage_angle) => editor.updateBus(bus.id, { voltage_angle })}
          />
        ) : null}
        <Button onClick={onSave} disabled={saving}>
          {saveLabel}
        </Button>
      </Section>
    );
  }

  if (selected.kind === 'line') {
    const line = grid.lines.find((item) => item.id === selected.id);
    if (!line) return null;
    return (
      <Section
        title={`Line ${line.id}`}
        action={
          <Button
            variant="danger"
            onClick={() => {
              editor.removeLine(line.id);
              onSelect(null);
            }}
          >
            Delete
          </Button>
        }
      >
        <TextField label="Name" value={line.name} onChange={(name) => editor.updateLine(line.id, { name })} />
        <SelectField
          label="From bus"
          value={line.from_bus}
          options={grid.buses.map((bus) => ({ value: bus.id, label: bus.id }))}
          onChange={(from_bus) => editor.updateLine(line.id, { from_bus })}
        />
        <SelectField
          label="To bus"
          value={line.to_bus}
          options={grid.buses.map((bus) => ({ value: bus.id, label: bus.id }))}
          onChange={(to_bus) => editor.updateLine(line.id, { to_bus })}
        />
        <NumberField label="Resistance (pu)" value={line.resistance} min={0} step={0.001} onChange={(resistance) => editor.updateLine(line.id, { resistance })} />
        <NumberField label="Reactance (pu)" value={line.reactance} step={0.001} onChange={(reactance) => editor.updateLine(line.id, { reactance })} />
        <NumberField label="Susceptance (pu)" value={line.susceptance} step={0.001} onChange={(susceptance) => editor.updateLine(line.id, { susceptance })} />
        <NumberField label="Thermal limit (MVA)" value={line.thermal_limit} min={1} suffix="MVA" onChange={(thermal_limit) => editor.updateLine(line.id, { thermal_limit })} />
        <Button onClick={onSave} disabled={saving}>
          {saveLabel}
        </Button>
      </Section>
    );
  }

  if (selected.kind === 'generator') {
    const generator = grid.generators.find((item) => item.id === selected.id);
    if (!generator) return null;
    const typeOptions = (Object.keys(GENERATOR_TYPE_LABELS) as GeneratorType[]).map((value) => ({
      value,
      label: GENERATOR_TYPE_LABELS[value],
    }));
    return (
      <Section
        title={`${generator.id} · ${GENERATOR_TYPE_LABELS[generator.type]}`}
        action={
          <Button
            variant="danger"
            onClick={() => {
              editor.removeGenerator(generator.id);
              onSelect(null);
            }}
          >
            Delete
          </Button>
        }
      >
        <TextField label="Name" value={generator.name} onChange={(name) => editor.updateGenerator(generator.id, { name })} />
        <SelectField
          label="Type"
          value={generator.type}
          options={typeOptions}
          onChange={(type) => editor.updateGenerator(generator.id, { type })}
        />
        <SelectField
          label="Bus"
          value={generator.bus_id}
          options={grid.buses.map((bus) => ({ value: bus.id, label: bus.id }))}
          onChange={(bus_id) => editor.updateGenerator(generator.id, { bus_id })}
        />
        <NumberField label="Current output (MW)" value={generator.active_power} suffix="MW" onChange={(active_power) => editor.updateGenerator(generator.id, { active_power })} />
        <NumberField label="Reactive output (MVAr)" value={generator.reactive_power} suffix="MVAr" onChange={(reactive_power) => editor.updateGenerator(generator.id, { reactive_power })} />
        <NumberField label="Min output (MW)" value={generator.active_power_min} suffix="MW" onChange={(active_power_min) => editor.updateGenerator(generator.id, { active_power_min })} />
        <NumberField label="Max output (MW)" value={generator.active_power_max} suffix="MW" onChange={(active_power_max) => editor.updateGenerator(generator.id, { active_power_max })} />
        {generator.type === 'STORAGE' ? (
          <NumberField label="Capacity (MWh)" value={generator.capacity_mwh} suffix="MWh" onChange={(capacity_mwh) => editor.updateGenerator(generator.id, { capacity_mwh })} />
        ) : null}
        <Button onClick={onSave} disabled={saving}>
          {saveLabel}
        </Button>
      </Section>
    );
  }

  const load = grid.loads.find((item) => item.id === selected.id);
  if (!load) return null;
  return (
    <Section
      title={`Load ${load.id}`}
      action={
        <Button
          variant="danger"
          onClick={() => {
            editor.removeLoad(load.id);
            onSelect(null);
          }}
        >
          Delete
        </Button>
      }
    >
      <TextField label="Name" value={load.name} onChange={(name) => editor.updateLoad(load.id, { name })} />
      <SelectField
        label="Bus"
        value={load.bus_id}
        options={grid.buses.map((bus) => ({ value: bus.id, label: bus.id }))}
        onChange={(bus_id) => editor.updateLoad(load.id, { bus_id })}
      />
      <NumberField label="Active power (MW)" value={load.active_power} suffix="MW" onChange={(active_power) => editor.updateLoad(load.id, { active_power })} />
      <NumberField label="Reactive power (MVAr)" value={load.reactive_power} suffix="MVAr" onChange={(reactive_power) => editor.updateLoad(load.id, { reactive_power })} />
      <Button onClick={onSave} disabled={saving}>
        {saveLabel}
      </Button>
    </Section>
  );
}
