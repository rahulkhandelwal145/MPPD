function InfoIcon({ note }) {
  return (
    <span className="relative group inline-flex items-center ml-1 cursor-pointer">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5 text-slate-400 hover:text-slate-600">
        <path fillRule="evenodd" d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0Zm-6 3.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0ZM7.293 5.293a1 1 0 1 1 1.414 1.414L8 7.414V9.5a.75.75 0 0 0 1.5 0V7a1 1 0 0 0-.293-.707l.586-.586V5.293Z" clipRule="evenodd" />
      </svg>
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 rounded-xl bg-slate-800 px-3 py-2 text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-lg">
        {note}
        <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
      </span>
    </span>
  );
}

export default function ScoreBar({ label, value, note }) {
  const score = typeof value === "number" ? value : 0;
  const percentage = Math.min(Math.max(score, 0), 100);
  const display = typeof value === "number" ? `${value.toFixed(1)} / 100` : "— / 100";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm font-medium text-slate-700">
        <span className="flex items-center">
          {label}
          {note && <InfoIcon note={note} />}
        </span>
        <span className="text-slate-900">{display}</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-200">
        <div
          className={`h-full rounded-full ${typeof value === "number" ? "bg-indigo-600" : "bg-slate-300"}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
