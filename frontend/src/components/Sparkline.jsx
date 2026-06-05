import { formatINR } from "../lib/format";

// Dependency-free line chart of declared assets over time. `points` is a
// chronological list of { year, assets }. Used compact on the MP card and
// larger (with axis labels) on the detail page.
export default function Sparkline({ points, width = 280, height = 64, showLabels = false }) {
  if (!points || points.length < 2) return null;

  const pad = showLabels ? 22 : 8;
  const padX = 10;
  const xs = points.map((p) => p.year);
  const ys = points.map((p) => p.assets);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys, 0);
  const maxY = Math.max(...ys);

  const sx = (v) => padX + (maxX === minX ? 0.5 : (v - minX) / (maxX - minX)) * (width - 2 * padX);
  const sy = (v) => height - pad - (maxY === minY ? 0.5 : (v - minY) / (maxY - minY)) * (height - pad - 8);

  const line = points.map((p, i) => `${i ? "L" : "M"}${sx(p.year).toFixed(1)},${sy(p.assets).toFixed(1)}`).join(" ");
  const area = `${line} L${sx(maxX).toFixed(1)},${(height - pad).toFixed(1)} L${sx(minX).toFixed(1)},${(height - pad).toFixed(1)} Z`;

  // Overall direction colours the trend (first → last point).
  const up = ys[ys.length - 1] >= ys[0];
  const stroke = up ? "#d97706" : "#0284c7";
  const fill = up ? "#fef3c7" : "#e0f2fe";
  const gid = `spark-${stroke.slice(1)}`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ height }} role="img" aria-label="Asset trajectory">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={fill} stopOpacity="0.9" />
          <stop offset="100%" stopColor={fill} stopOpacity="0.1" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gid})`} />
      <path d={line} fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      {points.map((p, i) => {
        const last = i === points.length - 1;
        return (
          <g key={i}>
            <circle cx={sx(p.year)} cy={sy(p.assets)} r={last ? 3.5 : 2.5} fill={last ? stroke : "#fff"} stroke={stroke} strokeWidth="1.5">
              <title>{`${p.year}: ${formatINR(p.assets)}`}</title>
            </circle>
            {showLabels && (
              <text x={sx(p.year)} y={height - 6} textAnchor="middle" className="fill-slate-400" style={{ fontSize: 10 }}>
                {p.year}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
