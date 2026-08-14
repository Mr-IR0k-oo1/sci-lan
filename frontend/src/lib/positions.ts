import type { Bus } from '../types';

export interface Point {
  x: number;
  y: number;
}

export function circlePosition(index: number, count: number): Point {
  const centerX = 640;
  const centerY = 340;
  const radius = Math.max(150, Math.min(260, count * 55));
  const angle = (index / Math.max(count, 1)) * Math.PI * 2 - Math.PI / 2;
  return {
    x: centerX + radius * Math.cos(angle),
    y: centerY + radius * Math.sin(angle),
  };
}

export function ensurePositions(buses: Bus[], prev: Record<string, Point>): Record<string, Point> {
  const next: Record<string, Point> = {};
  buses.forEach((bus, index) => {
    next[bus.id] = prev[bus.id] ?? circlePosition(index, buses.length);
  });
  return next;
}
