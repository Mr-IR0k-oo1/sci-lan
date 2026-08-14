import type { ComponentSelection, GridModel, ValidationIssue } from '../types';

function extractId(message: string): string | null {
  const match = message.match(/'([A-Za-z0-9_\- ]+)'/);
  return match ? match[1] : null;
}

function findById(grid: GridModel, id: string): ComponentSelection | null {
  if (grid.buses.some((bus) => bus.id === id)) return { kind: 'bus', id };
  if (grid.lines.some((line) => line.id === id)) return { kind: 'line', id };
  if (grid.generators.some((gen) => gen.id === id)) return { kind: 'generator', id };
  if (grid.loads.some((load) => load.id === id)) return { kind: 'load', id };
  if (grid.lines.some((line) => line.from_bus === id || line.to_bus === id)) {
    return { kind: 'bus', id };
  }
  return null;
}

export function issueTarget(issue: ValidationIssue, grid: GridModel): ComponentSelection | null {
  const mentioned = extractId(issue.message);
  if (mentioned) {
    const target = findById(grid, mentioned);
    if (target) return target;
  }

  switch (issue.code) {
    case 'missing_slack':
    case 'duplicate_bus_ids':
      if (grid.buses.length > 0) return { kind: 'bus', id: grid.buses[0].id };
      return null;
    case 'duplicate_line_ids':
      if (grid.lines.length > 0) return { kind: 'line', id: grid.lines[0].id };
      return null;
    default:
      return null;
  }
}
