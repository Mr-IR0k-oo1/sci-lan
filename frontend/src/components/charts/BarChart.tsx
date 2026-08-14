export interface BarDatum {
  label: string;
  value: number;
  className: string;
}

export function BarChart({
  title,
  data,
  max,
}: {
  title: string;
  data: BarDatum[];
  max?: number;
}) {
  if (data.length === 0) return null;
  const chartMax = max ?? Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="chart-block">
      <h4>{title}</h4>
      <div className="bar-chart">
        {data.map((datum) => (
          <div className="bar-row" key={datum.label}>
            <span className="bar-label">{datum.label}</span>
            <span className="bar-track">
              <span
                className={`bar-fill ${datum.className}`}
                style={{ width: `${Math.min(100, (datum.value / chartMax) * 100)}%` }}
                data-testid={`bar-${datum.label}`}
              />
            </span>
            <span className="bar-value">{datum.value.toFixed(1)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
