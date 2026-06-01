const VARIANTS = {
  default:  "bg-slate-100 text-slate-800",
  Minister: "bg-rose-100 text-rose-800",
  Speaker:  "bg-indigo-100 text-indigo-800",
  LOA:      "bg-amber-100 text-amber-800",
};

export default function ScoreBadge({ label }) {
  const cls = VARIANTS[label] ?? VARIANTS.default;
  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${cls}`}>
      {label}
    </span>
  );
}
