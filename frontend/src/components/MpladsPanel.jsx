import { formatINR } from "../lib/format";

function pct(n) {
  return n == null ? "—" : `${n.toFixed(n < 10 ? 1 : 0)}%`;
}

function StatCard({ label, value, accent }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-2 text-xl font-semibold tabular-nums ${accent ?? "text-slate-900"}`}>{value}</p>
    </div>
  );
}

// MPLADS local-area-development funds — raw constituency figures only. The
// percentile scores live on the list-page card; this panel keeps the stats.
// `mplads` is the sub-object from GET /mps/{slug} (null when no matched row).
export default function MpladsPanel({ mplads }) {
  if (!mplads) {
    return (
      <div className="mt-8 rounded-3xl bg-slate-50 p-5 text-slate-500">
        MPLADS fund data not available for this MP.
      </div>
    );
  }

  const {
    match_confidence,
    allocated_amount,
    total_expenditure,
    utilization_pct,
    completed_works,
    recommended_works,
    completion_rate_pct,
    transaction_count,
    successful_payments,
    pending_payments,
  } = mplads;

  return (
    <div className="mt-8 rounded-3xl bg-slate-50 p-5">
      <h2 className="text-lg font-semibold text-slate-900">MPLADS — Local Area Development</h2>
      <p className="mt-0.5 text-sm text-slate-500">Constituency development fund utilisation.</p>

      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard label="Allocated (incl. carry-forward)" value={formatINR(allocated_amount)} />
        <StatCard label="Total expenditure" value={formatINR(total_expenditure)} />
        <StatCard label="Utilisation" value={pct(utilization_pct)} />
        <StatCard label="Works completed" value={`${completed_works ?? "—"} / ${recommended_works ?? "—"}`} />
        <StatCard label="Completion rate" value={pct(completion_rate_pct)} />
        <StatCard label="Payments (success / total)" value={`${successful_payments ?? "—"} / ${transaction_count ?? "—"}`} />
        {pending_payments > 0 && (
          <StatCard label="Pending payments" value={pending_payments} accent="text-amber-700" />
        )}
      </div>

      <p className="mt-5 text-xs text-slate-400">
        Allocations include unspent carry-forward from the 17th Lok Sabha, so totals span more than the
        current term. Source: MPLADS / data.gov.in.
        {match_confidence && match_confidence !== "exact" && match_confidence !== "high" && (
          <span className="text-amber-600"> Name match to this MP is low-confidence.</span>
        )}
      </p>
    </div>
  );
}
