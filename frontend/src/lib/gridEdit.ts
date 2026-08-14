import type {
  Bus,
  Generator,
  GeneratorType,
  GridModel,
  Load,
  TransmissionLine,
} from '../types';

export function nextId(prefix: string, existing: string[]): string {
  const ids = new Set(existing);
  let n = 1;
  while (ids.has(`${prefix}${n}`)) n += 1;
  return `${prefix}${n}`;
}

export function copyGrid(grid: GridModel): GridModel {
  return {
    ...grid,
    buses: grid.buses.map((bus) => ({ ...bus })),
    lines: grid.lines.map((line) => ({ ...line })),
    generators: grid.generators.map((gen) => ({ ...gen })),
    loads: grid.loads.map((load) => ({ ...load })),
  };
}

export function generatorDefaults(
  type: GeneratorType,
  id: string,
  busId: string,
  name: string,
): Generator {
  const base = {
    id,
    bus_id: busId,
    type,
    active_power: 0,
    reactive_power: 0,
    capacity_mwh: 0,
  };
  switch (type) {
    case 'SOLAR':
      return {
        ...base,
        name: name || `${id} Solar`,
        active_power_min: 0,
        active_power_max: 100,
        reactive_power_min: -40,
        reactive_power_max: 40,
      };
    case 'WIND':
      return {
        ...base,
        name: name || `${id} Wind`,
        active_power_min: 0,
        active_power_max: 80,
        reactive_power_min: -30,
        reactive_power_max: 30,
      };
    case 'STORAGE':
      return {
        ...base,
        name: name || `${id} Battery`,
        active_power_min: -50,
        active_power_max: 50,
        reactive_power_min: -25,
        reactive_power_max: 25,
        capacity_mwh: 100,
      };
    default:
      return {
        ...base,
        name: name || `${id} Generator`,
        active_power_min: 0,
        active_power_max: 200,
        reactive_power_min: -60,
        reactive_power_max: 60,
      };
  }
}

export function addBus(grid: GridModel): { grid: GridModel; id: string } {
  const id = nextId('B', grid.buses.map((bus) => bus.id));
  const bus: Bus = {
    id,
    name: `Bus ${id}`,
    type: 'PQ',
    base_voltage: grid.buses[0]?.base_voltage ?? 138,
    voltage_magnitude: 1.0,
    voltage_angle: 0.0,
  };
  return { grid: { ...grid, buses: [...grid.buses, bus] }, id };
}

export function updateBus(grid: GridModel, id: string, patch: Partial<Bus>): GridModel {
  return {
    ...grid,
    buses: grid.buses.map((bus) => (bus.id === id ? { ...bus, ...patch } : bus)),
  };
}

export function removeBus(grid: GridModel, id: string): GridModel {
  return {
    ...grid,
    buses: grid.buses.filter((bus) => bus.id !== id),
    lines: grid.lines.filter((line) => line.from_bus !== id && line.to_bus !== id),
    generators: grid.generators.filter((gen) => gen.bus_id !== id),
    loads: grid.loads.filter((load) => load.bus_id !== id),
  };
}

export function addLine(
  grid: GridModel,
  fromBus: string,
  toBus: string,
): { grid: GridModel; id: string | null } {
  if (fromBus === toBus) return { grid, id: null };
  const id = nextId('L', grid.lines.map((line) => line.id));
  const line: TransmissionLine = {
    id,
    name: `Line ${id}`,
    from_bus: fromBus,
    to_bus: toBus,
    resistance: 0.01,
    reactance: 0.05,
    susceptance: 0.0,
    thermal_limit: 100,
  };
  return { grid: { ...grid, lines: [...grid.lines, line] }, id };
}

export function updateLine(
  grid: GridModel,
  id: string,
  patch: Partial<TransmissionLine>,
): GridModel {
  return {
    ...grid,
    lines: grid.lines.map((line) => (line.id === id ? { ...line, ...patch } : line)),
  };
}

export function removeLine(grid: GridModel, id: string): GridModel {
  return { ...grid, lines: grid.lines.filter((line) => line.id !== id) };
}

export function addGenerator(
  grid: GridModel,
  busId: string,
  type: GeneratorType,
): { grid: GridModel; id: string } {
  const id = nextId('G', grid.generators.map((gen) => gen.id));
  const generator = generatorDefaults(type, id, busId, '');
  return { grid: { ...grid, generators: [...grid.generators, generator] }, id };
}

export function updateGenerator(grid: GridModel, id: string, patch: Partial<Generator>): GridModel {
  return {
    ...grid,
    generators: grid.generators.map((gen) => (gen.id === id ? { ...gen, ...patch } : gen)),
  };
}

export function removeGenerator(grid: GridModel, id: string): GridModel {
  return { ...grid, generators: grid.generators.filter((gen) => gen.id !== id) };
}

export function addLoad(grid: GridModel, busId: string): { grid: GridModel; id: string } {
  const id = nextId('D', grid.loads.map((load) => load.id));
  const load: Load = {
    id,
    name: `Load ${id}`,
    bus_id: busId,
    active_power: 10,
    reactive_power: 5,
  };
  return { grid: { ...grid, loads: [...grid.loads, load] }, id };
}

export function updateLoad(grid: GridModel, id: string, patch: Partial<Load>): GridModel {
  return {
    ...grid,
    loads: grid.loads.map((load) => (load.id === id ? { ...load, ...patch } : load)),
  };
}

export function removeLoad(grid: GridModel, id: string): GridModel {
  return { ...grid, loads: grid.loads.filter((load) => load.id !== id) };
}
