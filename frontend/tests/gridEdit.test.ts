import { describe, expect, it } from 'vitest';
import type { GridModel } from '../src/types';
import {
  addBus,
  addGenerator,
  addLine,
  addLoad,
  copyGrid,
  nextId,
  removeBus,
  removeGenerator,
  updateBus,
  updateGenerator,
} from '../src/lib/gridEdit';

function baseGrid(): GridModel {
  return {
    grid_id: 'test',
    name: 'Test Grid',
    base_mva: 100,
    buses: [
      { id: 'B1', name: 'Slack', type: 'SLACK', base_voltage: 138, voltage_magnitude: 1.0, voltage_angle: 0.0 },
      { id: 'B2', name: 'Load Bus', type: 'PQ', base_voltage: 138, voltage_magnitude: 1.0, voltage_angle: 0.0 },
    ],
    lines: [
      { id: 'L1', name: 'Line L1', from_bus: 'B1', to_bus: 'B2', resistance: 0.01, reactance: 0.05, susceptance: 0, thermal_limit: 100 },
    ],
    generators: [
      { id: 'G1', name: 'G1', bus_id: 'B1', type: 'CONVENTIONAL', active_power: 0, reactive_power: 0, active_power_min: 0, active_power_max: 200, reactive_power_min: -60, reactive_power_max: 60, capacity_mwh: 0 },
    ],
    loads: [],
  };
}

describe('gridEdit', () => {
  it('generates unique sequential ids', () => {
    expect(nextId('B', ['B1', 'B2', 'B3'])).toBe('B4');
    expect(nextId('L', ['L1'])).toBe('L2');
    expect(nextId('G', [])).toBe('G1');
  });

  it('adds a bus without mutating the original grid', () => {
    const grid = baseGrid();
    const result = addBus(grid);
    expect(result.id).toBe('B3');
    expect(result.grid.buses).toHaveLength(3);
    expect(result.grid.buses[2].type).toBe('PQ');
    expect(grid.buses).toHaveLength(2);
  });

  it('adds a line between two buses', () => {
    const grid = baseGrid();
    const { grid: next, id } = addLine(grid, 'B1', 'B2');
    expect(id).toBe('L2');
    expect(next.lines).toHaveLength(2);
    expect(next.lines[1]).toMatchObject({ from_bus: 'B1', to_bus: 'B2' });
  });

  it('refuses a self-loop line', () => {
    const grid = baseGrid();
    const { grid: next, id } = addLine(grid, 'B1', 'B1');
    expect(id).toBeNull();
    expect(next.lines).toHaveLength(1);
  });

  it('removes a bus and its attached equipment', () => {
    const grid = baseGrid();
    const withLoad = addLoad(grid, 'B2');
    const withGen = addGenerator(withLoad.grid, 'B2', 'SOLAR');
    const next = removeBus(withGen.grid, 'B2');
    expect(next.buses.map((bus) => bus.id)).toEqual(['B1']);
    expect(next.lines).toHaveLength(0);
    expect(next.generators.map((gen) => gen.id)).toEqual(['G1']);
    expect(next.loads).toHaveLength(0);
  });

  it('updates a bus immutably', () => {
    const grid = baseGrid();
    const next = updateBus(grid, 'B2', { type: 'PV', voltage_magnitude: 1.03 });
    expect(next.buses[1]).toMatchObject({ id: 'B2', type: 'PV', voltage_magnitude: 1.03 });
    expect(grid.buses[1].type).toBe('PQ');
  });

  it('creates storage generators with battery limits', () => {
    const grid = baseGrid();
    const { grid: next, id } = addGenerator(grid, 'B2', 'STORAGE');
    const battery = next.generators.find((gen) => gen.id === id);
    expect(battery).toBeDefined();
    expect(battery?.type).toBe('STORAGE');
    expect(battery?.active_power_min).toBe(-50);
    expect(battery?.active_power_max).toBe(50);
    expect(battery?.capacity_mwh).toBe(100);
  });

  it('copyGrid deep-copies so mutations stay isolated', () => {
    const grid = baseGrid();
    const copy = copyGrid(grid);
    copy.buses[0].name = 'Changed';
    expect(grid.buses[0].name).toBe('Slack');
  });

  it('removeGenerator only removes the targeted generator', () => {
    const grid = baseGrid();
    const added = addGenerator(grid, 'B2', 'WIND');
    const next = removeGenerator(added.grid, added.id);
    expect(next.generators.map((gen) => gen.id)).toEqual(['G1']);
  });

  it('updateGenerator does not touch other generators', () => {
    const grid = baseGrid();
    const added = addGenerator(grid, 'B2', 'SOLAR');
    const next = updateGenerator(added.grid, added.id, { active_power: 42 });
    const solar = next.generators.find((gen) => gen.id === added.id);
    const base = next.generators.find((gen) => gen.id === 'G1');
    expect(solar?.active_power).toBe(42);
    expect(base?.active_power).toBe(0);
  });
});
