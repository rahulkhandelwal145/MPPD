export default function ScoreBadge({ label }) {
  return (
    <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-800">
      {label}
    </span>
  );
}
