export default function ScoreBar({ label, value, note }) {
  const score = typeof value === "number" ? value : 0;
  const percentage = Math.min(Math.max(score, 0), 100);
  const display = typeof value === "number" ? `${value.toFixed(1)} / 100` : "— / 100";

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm font-medium text-slate-700">
        <span>{label}</span>
        <span className="text-slate-900">{display}</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-200">
        <div
          className={`h-full rounded-full ${typeof value === "number" ? "bg-indigo-600" : "bg-slate-300"}`}
          style={{ width: `${percentage}%` }}
          title={note}
        />
      </div>
      {note ? <p className="text-xs text-slate-500">{note}</p> : null}
    </div>
  );
}
