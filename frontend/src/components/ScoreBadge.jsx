const VARIANTS = {
  default:  "bg-slate-100 text-slate-700 ring-slate-200",
  Minister: "bg-rose-50 text-rose-700 ring-rose-200",
  Speaker:  "bg-indigo-50 text-indigo-700 ring-indigo-200",
  LOA:      "bg-amber-50 text-amber-700 ring-amber-200",
};

export default function ScoreBadge({ label }) {
  const cls = VARIANTS[label] ?? VARIANTS.default;
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wide ring-1 ${cls}`}>
      {label}
    </span>
  );
}
