import StatementFlag from "./StatementFlag";

const GROUP_BORDER = {
  A: "border-red-200",
  B: "border-orange-200",
  C: "border-amber-200",
  D: "border-green-200",
};

function formatDate(value) {
  if (!value) return "Date unknown";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "Date unknown";
  return d.toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" });
}

// One classified statement. `flagged` toggles the "Why flagged" block (A/B/C);
// constructive (D) cards omit it. Confidence shows on hover per spec.
export default function StatementCard({ statement, flagged }) {
  const {
    category,
    category_label,
    verbatim,
    constitutional_anchor,
    data_contradicted,
    reason,
    source,
    article_url,
    published_at,
    confidence,
  } = statement;

  const border = GROUP_BORDER[category?.[0]] ?? "border-slate-200";

  return (
    <div className={`group/stmt relative rounded-3xl border bg-white p-5 shadow-soft ${border}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <StatementFlag category={category} label={category_label} />
        {confidence != null && (
          <span className="pointer-events-none rounded-full bg-slate-900 px-2 py-1 text-[11px] font-medium text-white opacity-0 transition-opacity group-hover/stmt:opacity-100">
            {confidence}% confidence
          </span>
        )}
      </div>

      <p className="mt-2 text-xs text-slate-400">
        {formatDate(published_at)}
        {source ? ` · ${source}` : ""}
      </p>

      <blockquote className="mt-3 border-l-2 border-slate-200 pl-4 text-[15px] leading-relaxed text-slate-800">
        “{verbatim}”
      </blockquote>

      {flagged && (
        <div className="mt-4 rounded-2xl bg-slate-50 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Why flagged</p>
          {(constitutional_anchor || data_contradicted) && (
            <p className="mt-1 text-sm font-medium text-slate-700">
              {[constitutional_anchor, data_contradicted].filter(Boolean).join(" · ")}
            </p>
          )}
          {reason && <p className="mt-1 text-sm text-slate-600">{reason}</p>}
        </div>
      )}

      {article_url && (
        <a
          href={article_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-brand-700 transition hover:text-brand-900"
        >
          Read full article <span aria-hidden>→</span>
        </a>
      )}
    </div>
  );
}
