import { useCallback, useEffect, useRef, useState } from 'react';
import type { Point } from '../../lib/positions';
import type {
  ComponentSelection,
  GridModel,
  PowerFlowResult,
} from '../../types';
import type { GridEditor } from '../../state/GridContext';

const BUS_RADIUS = 16;

const TYPE_FILL: Record<string, string> = {
  SLACK: '#1d4ed8',
  PV: '#047857',
  PQ: '#475569',
};

const STATUS_COLOR: Record<string, string> = {
  NORMAL: '#64748b',
  WARNING: '#f59e0b',
  OVERLOADED: '#dc2626',
  CRITICAL: '#dc2626',
};

interface GridCanvasProps {
  grid: GridModel;
  positions: Record<string, Point>;
  editor: GridEditor;
  result: PowerFlowResult | null;
  selected: ComponentSelection | null;
  onSelect: (selection: ComponentSelection | null) => void;
  lineToolActive: boolean;
  lineFrom: string | null;
  setLineFrom: (busId: string | null) => void;
}

export function GridCanvas({
  grid,
  positions,
  editor,
  result,
  selected,
  onSelect,
  lineToolActive,
  lineFrom,
  setLineFrom,
}: GridCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [size, setSize] = useState({ width: 800, height: 500 });
  const [dragBus, setDragBus] = useState<string | null>(null);
  const [cursor, setCursor] = useState<Point | null>(null);

  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;
    const update = () => setSize({ width: node.clientWidth, height: node.clientHeight });
    update();
    const observer = new ResizeObserver(update);
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    containerRef.current?.focus();
  }, [grid.grid_id]);

  const svgPoint = useCallback((clientX: number, clientY: number): Point => {
    const svg = svgRef.current;
    if (!svg) return { x: 0, y: 0 };
    const rect = svg.getBoundingClientRect();
    return {
      x: ((clientX - rect.left) / rect.width) * size.width,
      y: ((clientY - rect.top) / rect.height) * size.height,
    };
  }, [size]);

  const busResults = useRef(
    new Map(result?.buses.map((bus) => [bus.bus_id, bus]) ?? []),
  );
  busResults.current = new Map(result?.buses.map((bus) => [bus.bus_id, bus]) ?? []);
  const lineResults = new Map(result?.lines.map((line) => [line.line_id, line]) ?? []);

  const handleBusClick = useCallback(
    (busId: string) => {
      if (lineToolActive) {
        if (!lineFrom) {
          setLineFrom(busId);
          return;
        }
        if (lineFrom === busId) {
          setLineFrom(null);
          return;
        }
        editor.addLine(lineFrom, busId);
        setLineFrom(null);
        return;
      }
      onSelect({ kind: 'bus', id: busId });
    },
    [lineToolActive, lineFrom, setLineFrom, editor, onSelect],
  );

  const handlePointerMove = useCallback(
    (event: React.PointerEvent<SVGSVGElement>) => {
      const point = svgPoint(event.clientX, event.clientY);
      if (dragBus) {
        editor.moveBus(dragBus, point.x, point.y);
      } else {
        setCursor(point);
      }
    },
    [svgPoint, dragBus, editor],
  );

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (event.key === 'Escape') {
        setLineFrom(null);
        onSelect(null);
        return;
      }
      if (event.key === 'Delete' || event.key === 'Backspace') {
        if (!selected) return;
        event.preventDefault();
        const { kind, id } = selected;
        if (kind === 'bus') editor.removeBus(id);
        else if (kind === 'line') editor.removeLine(id);
        else if (kind === 'generator') editor.removeGenerator(id);
        else if (kind === 'load') editor.removeLoad(id);
        onSelect(null);
      }
    },
    [selected, editor, onSelect, setLineFrom],
  );

  const fromPosition = lineFrom ? positions[lineFrom] : null;
  const attachments: Record<
    string,
    { generators: { id: string; label: string; type: string }[]; loads: { id: string; label: string }[] }
  > = {};
  grid.generators.forEach((gen) => {
    const entry = (attachments[gen.bus_id] ??= { generators: [], loads: [] });
    entry.generators.push({ id: gen.id, label: gen.id, type: gen.type });
  });
  grid.loads.forEach((load) => {
    const entry = (attachments[load.bus_id] ??= { generators: [], loads: [] });
    entry.loads.push({ id: load.id, label: load.id });
  });

  return (
    <div
      ref={containerRef}
      className="canvas-scroll"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      data-testid="grid-canvas"
    >
      <div className="grid-canvas">
        <svg
          ref={svgRef}
          className="canvas-svg"
          viewBox={`0 0 ${size.width} ${size.height}`}
          preserveAspectRatio="none"
          onPointerMove={handlePointerMove}
          onPointerUp={() => setDragBus(null)}
          onPointerLeave={() => setCursor(null)}
        >
          <rect
            width={size.width}
            height={size.height}
            fill="transparent"
            onClick={() => {
              if (!lineToolActive) onSelect(null);
            }}
          />

          {grid.lines.map((line) => {
            const from = positions[line.from_bus];
            const to = positions[line.to_bus];
            if (!from || !to) return null;
            const lineResult = lineResults.get(line.id);
            const status = lineResult?.status ?? 'NORMAL';
            const isSelected = selected?.kind === 'line' && selected.id === line.id;
            return (
              <g
                key={line.id}
                className="canvas-line"
                onClick={(event) => {
                  event.stopPropagation();
                  onSelect({ kind: 'line', id: line.id });
                }}
                data-testid={`line-${line.id}`}
              >
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke={STATUS_COLOR[status]}
                  strokeWidth={isSelected ? 5 : 3}
                  strokeLinecap="round"
                />
                {lineResult ? (
                  <text
                    x={(from.x + to.x) / 2}
                    y={(from.y + to.y) / 2 - 6}
                    textAnchor="middle"
                    fontSize="10"
                    fill="#334155"
                    className="canvas-label"
                  >
                    {lineResult.loading_percentage.toFixed(1)}%
                  </text>
                ) : null}
              </g>
            );
          })}

          {lineToolActive && fromPosition && cursor ? (
            <line
              x1={fromPosition.x}
              y1={fromPosition.y}
              x2={cursor.x}
              y2={cursor.y}
              stroke="#2563eb"
              strokeWidth={2}
              strokeDasharray="6 4"
            />
          ) : null}

          {grid.buses.map((bus) => {
            const position = positions[bus.id];
            if (!position) return null;
            const busResult = busResults.current.get(bus.id);
            const status = busResult?.status;
            const isSelected = selected?.kind === 'bus' && selected.id === bus.id;
            const isFrom = lineFrom === bus.id;
            const stroke = status
              ? STATUS_COLOR[status]
              : isSelected
                ? '#2563eb'
                : isFrom
                  ? '#2563eb'
                  : '#0f172a';
            const attachment = attachments[bus.id];
            const attachCount =
              (attachment ? attachment.generators.length + attachment.loads.length : 0) + 1;
            return (
              <g key={bus.id}>
                {attachment
                  ? [
                      ...attachment.generators.map((gen, index) => {
                        const angle = (index + 0.35) * ((Math.PI * 2) / attachCount);
                        const x = position.x + Math.cos(angle) * 34;
                        const y = position.y + Math.sin(angle) * 34;
                        return (
                          <g
                            key={gen.id}
                            className="canvas-attachment"
                            onClick={(event) => {
                              event.stopPropagation();
                              onSelect({ kind: 'generator', id: gen.id });
                            }}
                            data-testid={`gen-${gen.id}`}
                          >
                            <circle cx={x} cy={y} r={9} fill="#f59e0b" stroke="#92400e" strokeWidth={1.5} />
                            <text x={x} y={y + 3} textAnchor="middle" fontSize="9" fill="#ffffff">
                              {gen.type === 'SOLAR' ? 'S' : gen.type === 'WIND' ? 'W' : gen.type === 'STORAGE' ? 'B' : 'G'}
                            </text>
                          </g>
                        );
                      }),
                      ...attachment.loads.map((load, index) => {
                        const angle = (index + 0.7) * ((Math.PI * 2) / attachCount);
                        const x = position.x + Math.cos(angle) * 34;
                        const y = position.y + Math.sin(angle) * 34;
                        return (
                          <g
                            key={load.id}
                            className="canvas-attachment"
                            onClick={(event) => {
                              event.stopPropagation();
                              onSelect({ kind: 'load', id: load.id });
                            }}
                            data-testid={`load-${load.id}`}
                          >
                            <path
                              d={`M ${x - 8} ${y - 6} L ${x + 8} ${y - 6} L ${x} ${y + 8} Z`}
                              fill="#a855f7"
                              stroke="#581c87"
                              strokeWidth={1.5}
                            />
                          </g>
                        );
                      }),
                    ]
                  : null}
                <g
                  className="canvas-bus"
                  onClick={(event) => {
                    event.stopPropagation();
                    handleBusClick(bus.id);
                  }}
                  onPointerDown={(event) => {
                    if (lineToolActive) return;
                    event.stopPropagation();
                    try {
                      event.currentTarget.setPointerCapture(event.pointerId);
                    } catch {
                      // pointer capture is not available in all environments
                    }
                    onSelect({ kind: 'bus', id: bus.id });
                    setDragBus(bus.id);
                  }}
                  data-testid={`bus-${bus.id}`}
                  aria-label={`Bus ${bus.id}`}
                  role="button"
                >
                  <circle
                    cx={position.x}
                    cy={position.y}
                    r={BUS_RADIUS}
                    fill={TYPE_FILL[bus.type] ?? '#475569'}
                    stroke={stroke}
                    strokeWidth={isSelected || isFrom ? 4 : 2}
                  />
                  <text x={position.x} y={position.y + 4} textAnchor="middle" fontSize="10" fill="#ffffff">
                    {bus.id}
                  </text>
                  <text
                    x={position.x}
                    y={position.y - BUS_RADIUS - 6}
                    textAnchor="middle"
                    fontSize="10"
                    fill={status ? STATUS_COLOR[status] : '#334155'}
                    className="canvas-label"
                  >
                    {busResult
                      ? `${busResult.voltage_magnitude.toFixed(3)} pu`
                      : `${bus.type}`}
                  </text>
                </g>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
