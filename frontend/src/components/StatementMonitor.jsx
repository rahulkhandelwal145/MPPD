import useStatements from "../hooks/useStatements";
import StatementCard from "./StatementCard";

function EmptyState() {
  return (
    <div className="rounded-3xl bg-white p-5 text-sm text-slate-500">
      No statements from major English outlets found in the last 90 days. This
      does not reflect the MP&apos;s local or vernacular media presence.
    </div>
  );
}

// Public Statement Monitor — display only, never part of any score. Shown below
// the integrity section on the MP profile. Flagged = A/B/C, constructive = D;
// category E is never returned by the API.
export default function StatementMonitor({ slug }) {
  const { loading, data, error, notFound } = useStatements(slug);

  if (loading) {
    return <div className="mt-8 rounded-3xl bg-slate-50 p-5 text-slate-600">Loading statement monitor…</div>;
  }

  if (error) {
    return (
      <div className="mt-8 rounded-3xl border border-red-200 bg-red-50 p-5 text-red-700">
        Unable to load statement monitor.
      </div>
    );
  }

  const flagged = (!notFound && data?.flagged) || [];
  const constructive = (!notFound && data?.constructive) || [];
  const hasNone = flagged.length === 0 && constructive.length === 0;

  return (
    <div className="mt-8 rounded-3xl bg-slate-50 p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-900">Public Statement Monitor</h2>
        <p className="text-xs text-slate-500">Last 90 days · Direct quotes only</p>
      </div>

      <div className="mt-5 space-y-6">
        {hasNone && <EmptyState />}

        {flagged.length > 0 && (
          <section>
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
              <span aria-hidden>⚠️</span> Flagged Statements ({flagged.length})
            </h3>
            <div className="space-y-3">
              {flagged.map((s) => (
                <StatementCard key={s.id} statement={s} flagged />
              ))}
            </div>
          </section>
        )}

        {constructive.length > 0 && (
          <section>
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
              <span aria-hidden>✅</span> Constructive Statements ({constructive.length})
            </h3>
            <div className="space-y-3">
              {constructive.map((s) => (
                <StatementCard key={s.id} statement={s} flagged={false} />
              ))}
            </div>
          </section>
        )}

        <section className="rounded-3xl border border-slate-200 bg-white p-4">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <span aria-hidden>ℹ️</span> About this monitor
          </h3>
          <p className="mt-2 text-xs leading-relaxed text-slate-500">
            {data?.disclaimer ??
              "Analyses direct quotes from major English news outlets only. Flags statements that contradict the Indian Constitution, scientific consensus, or the government's own documented data. Political opinions are never flagged. Only verbatim quotes are analysed. Always read the linked source article."}
          </p>
          <p className="mt-2 text-xs font-medium text-slate-400">
            ⚡ AI-powered · May contain errors · Regional-language coverage not included
          </p>
        </section>
      </div>
    </div>
  );
}
