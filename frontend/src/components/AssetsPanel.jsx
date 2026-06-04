import { formatINR } from "../lib/format";

const CRORE = 10_000_000;

// 1–5 bags by wealth tier: <1Cr, 1–5Cr, 5–25Cr, 25–100Cr, >100Cr.
function bagCount(total) {
  if (total == null) return 0;
  const cr = total / CRORE;
  if (cr < 1) return 1;
  if (cr < 5) return 2;
  if (cr < 25) return 3;
  if (cr < 100) return 4;
  return 5;
}

function MoneyBag({ filled }) {
  return (
    <svg viewBox="0 0 24 24" className={`h-7 w-7 ${filled ? "text-emerald-600" : "text-slate-200"}`} fill="currentColor" aria-hidden="true">
      <path d="M9 2h6l-1.2 2.2c2.9 1.1 5.2 4.2 5.2 8.3 0 5-3.2 7.5-7 7.5s-7-2.5-7-7.5c0-4.1 2.3-7.2 5.2-8.3L9 2Zm3 6.5c-1.5 0-2.5.9-2.5 2 0 .9.6 1.5 1.8 1.8l1.1.3c.5.1.6.3.6.5 0 .3-.3.5-.9.5-.7 0-1.1-.2-1.3-.7l-1.4.6c.3.9 1.1 1.4 2 1.5V16h1.3v-1.2c1.4-.2 2.3-1 2.3-2.1 0-.9-.5-1.5-1.8-1.8l-1.1-.3c-.5-.1-.7-.3-.7-.5 0-.3.3-.4.8-.4.6 0 1 .2 1.1.6l1.4-.6c-.3-.8-1-1.2-1.8-1.3V7h-1.3v1.5Z" />
    </svg>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-semibold text-slate-900">{formatINR(value)}</p>
    </div>
  );
}

export default function AssetsPanel({ assets, education }) {
  const {
    total_assets,
    movable_assets,
    immovable_assets,
    total_liabilities,
    self_income,
    spouse_income,
    history = [],
  } = assets || {};

  const bags = bagCount(total_assets);

  return (
    <div className="space-y-5">
      {/* Money bags + total */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-1">
          {[0, 1, 2, 3, 4].map((i) => (
            <MoneyBag key={i} filled={i < bags} />
          ))}
        </div>
        <div className="sm:text-right">
          <p className="text-sm text-slate-500">Total declared assets</p>
          <p className="text-2xl font-semibold text-slate-900">{formatINR(total_assets)}</p>
        </div>
      </div>

      {/* Figures */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard label="Total assets" value={total_assets} />
        <StatCard label="Movable assets" value={movable_assets} />
        <StatCard label="Immovable assets" value={immovable_assets} />
        <StatCard label="Total liabilities" value={total_liabilities} />
        <StatCard label="Self income" value={self_income} />
        <StatCard label="Spouse income" value={spouse_income} />
      </div>

      {education && (
        <p className="text-sm text-slate-600">
          <span className="font-medium text-slate-700">Education:</span> {education}
        </p>
      )}

      {/* Asset history */}
      {history.length > 0 && (
        <div>
          <p className="text-sm font-medium text-slate-700">Asset history</p>
          <ul className="mt-2 space-y-2 border-l-2 border-slate-200 pl-4">
            {history.map((h, i) => (
              <li key={i} className="flex items-center justify-between text-sm">
                <span className="text-slate-600">{h.election}</span>
                <span className="font-medium text-slate-900">{formatINR(h.assets_rupees)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
