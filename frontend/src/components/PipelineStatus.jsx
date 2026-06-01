export default function PipelineStatus({ lastRun }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Pipeline status</h3>
      <div className="mt-3 space-y-2 text-sm text-slate-700">
        <div className="flex items-center justify-between">
          <span>Last updated</span>
          <span>{lastRun?.last_run_at ? new Date(lastRun.last_run_at).toLocaleString() : "Never"}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Status</span>
          <span>{lastRun?.last_run_status ?? "Unknown"}</span>
        </div>
      </div>
    </div>
  );
}
