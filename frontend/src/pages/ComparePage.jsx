import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { fetchMP } from "../lib/api";
import PartyTag from "../components/PartyTag";
import { useCompare } from "../context/CompareContext";
import { formatINR, formatPctChange } from "../lib/format";

// ─── helpers ─────────────────────────────────────────────────────────────────

function ordinal(n) {
  if (n == null) return "—";
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function highlights(values, higherIsBetter) {
  const nums = values.map((v) => (v != null && typeof v === "number" ? v : null));
  const defined = nums.filter((v) => v !== null);
  if (defined.length < 2) return nums.map(() => null);
  const best = higherIsBetter ? Math.max(...defined) : Math.min(...defined);
  const worst = higherIsBetter ? Math.min(...defined) : Math.max(...defined);
  if (best === worst) return nums.map(() => null);
  return nums.map((v) => (v === null ? null : v === best ? "best" : v === worst ? "worst" : null));
}

function tone(v) {
  if (typeof v !== "number") return { bar: "bg-slate-200", text: "text-slate-400" };
  if (v >= 67) return { bar: "bg-gradient-to-r from-emerald-400 to-emerald-600", text: "text-emerald-600" };
  if (v >= 34) return { bar: "bg-gradient-to-r from-amber-400 to-amber-500", text: "text-amber-600" };
  return { bar: "bg-gradient-to-r from-rose-400 to-rose-500", text: "text-rose-600" };
}

function getScore(mp, key) {
  return mp.scores?.[key] ?? mp[key] ?? null;
}

// ─── table building blocks ───────────────────────────────────────────────────

function SectionHeader({ label, colSpan }) {
  return (
    <tr>
      <td
        colSpan={colSpan}
        className="bg-slate-50 px-4 py-2 text-[11px] font-bold uppercase tracking-widest text-slate-400"
      >
        {label}
      </td>
    </tr>
  );
}

function LabelCell({ children }) {
  return (
    <td className="sticky left-0 z-10 min-w-[140px] border-r border-slate-100 bg-white px-4 py-3 text-sm font-medium whitespace-nowrap text-slate-600">
      {children}
    </td>
  );
}

function ScoreCell({ value, hl }) {
  const v = typeof value === "number" ? value : null;
  const pct = v != null ? Math.min(Math.max(v, 0), 100) : 0;
  const t = tone(v);
  const bg = hl === "best" ? "bg-emerald-50" : hl === "worst" ? "bg-rose-50/60" : "";
  return (
    <td className={`px-4 py-3 text-center transition-colors ${bg}`}>
      <div className={`font-bold tabular-nums text-base ${t.text}`}>
        {v != null ? v.toFixed(1) : "N/A"}
        {v != null && <span className="ml-0.5 text-xs font-normal text-slate-400">/100</span>}
      </div>
      <div className="mx-auto mt-1.5 h-1.5 max-w-[72px] overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${t.bar} transition-[width] duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {hl === "best" && <div className="mt-1 text-[10px] font-semibold text-emerald-600">▲ Best</div>}
      {hl === "worst" && <div className="mt-1 text-[10px] font-semibold text-rose-500">▼ Lowest</div>}
    </td>
  );
}

function DataCell({ children, hl }) {
  const bg = hl === "best" ? "bg-emerald-50" : hl === "worst" ? "bg-rose-50/60" : "";
  return (
    <td className={`px-4 py-3 text-center text-sm transition-colors ${bg}`}>
      {children ?? "—"}
    </td>
  );
}

function ScoreRow({ label, mps, getValue }) {
  const values = mps.map(getValue);
  const hls = highlights(values, true);
  return (
    <tr className="border-t border-slate-100">
      <LabelCell>{label}</LabelCell>
      {mps.map((mp, i) => (
        <ScoreCell key={mp.prs_slug} value={values[i]} hl={hls[i]} />
      ))}
    </tr>
  );
}

function DataRow({ label, mps, getValue, higherIsBetter = null, format }) {
  const values = mps.map(getValue);
  const hls = higherIsBetter != null ? highlights(values, higherIsBetter) : values.map(() => null);
  return (
    <tr className="border-t border-slate-100">
      <LabelCell>{label}</LabelCell>
      {mps.map((mp, i) => (
        <DataCell key={mp.prs_slug} hl={hls[i]}>
          {values[i] != null ? (format ? format(values[i]) : String(values[i])) : "—"}
        </DataCell>
      ))}
    </tr>
  );
}

function TextRow({ label, mps, getValue }) {
  return (
    <tr className="border-t border-slate-100">
      <LabelCell>{label}</LabelCell>
      {mps.map((mp) => (
        <td key={mp.prs_slug} className="px-4 py-3 text-center text-sm text-slate-700">
          {getValue(mp) ?? "—"}
        </td>
      ))}
    </tr>
  );
}

// ─── MP header cell ───────────────────────────────────────────────────────────

function MPHeaderCell({ mp, onRemove }) {
  const role = mp.is_speaker ? "Speaker" : mp.is_loa ? "LOA" : mp.is_minister ? "Minister" : null;
  return (
    <th className="min-w-[190px] bg-white px-4 py-4 text-center align-top font-normal">
      <div className="flex flex-col items-center gap-2">
        {mp.image_url ? (
          <img
            src={mp.image_url}
            alt={mp.name}
            className="h-16 w-16 rounded-2xl object-cover object-top ring-2 ring-slate-100"
          />
        ) : (
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-gradient text-xl font-bold text-white">
            {mp.name.charAt(0)}
          </div>
        )}
        <Link
          to={`/mp/${mp.prs_slug}`}
          className="font-display text-sm font-bold leading-snug text-slate-900 transition-colors hover:text-brand-700"
        >
          {mp.name}
        </Link>
        <p className="text-xs text-slate-500">{mp.constituency}, {mp.state}</p>
        <PartyTag party={mp.party} />
        {role && (
          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
            {role}
          </span>
        )}
        <button
          onClick={() => onRemove(mp.prs_slug)}
          className="rounded-full px-2.5 py-0.5 text-xs text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
        >
          ✕ Remove
        </button>
      </div>
    </th>
  );
}

// ─── page ─────────────────────────────────────────────────────────────────────

export default function ComparePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { removeMP } = useCompare();

  const slugs = useMemo(() => {
    const p = new URLSearchParams(location.search);
    return (p.get("mps") ?? "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .slice(0, 5);
  }, [location.search]);

  const [mps, setMps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slugs.length) { setLoading(false); return; }
    setLoading(true);
    Promise.allSettled(slugs.map((s) => fetchMP(s)))
      .then((results) => {
        setMps(results.filter((r) => r.status === "fulfilled").map((r) => r.value));
      })
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slugs.join(",")]);

  const handleRemove = (slug) => {
    removeMP(slug);
    const remaining = slugs.filter((s) => s !== slug);
    if (remaining.length < 2) navigate(remaining.length === 1 ? `/mp/${remaining[0]}` : "/");
    else navigate(`/compare?mps=${remaining.join(",")}`);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-10 w-48 rounded-2xl" />
        <div className="skeleton h-[600px] rounded-4xl" />
      </div>
    );
  }

  if (!slugs.length || mps.length === 0) {
    return (
      <div className="rounded-4xl border border-slate-200 bg-white p-12 text-center shadow-soft">
        <p className="text-lg font-semibold text-slate-700">No MPs selected for comparison</p>
        <p className="mt-2 text-sm text-slate-500">
          Use the <span className="font-medium text-brand-600">+ Compare</span> button on any MP card to add them.
        </p>
        <Link
          to="/"
          className="mt-6 inline-flex items-center gap-1.5 rounded-full bg-brand-gradient px-6 py-2 text-sm font-semibold text-white shadow-soft transition hover:opacity-90"
        >
          Browse MPs →
        </Link>
      </div>
    );
  }

  if (mps.length < 2) {
    return (
      <div className="rounded-4xl border border-amber-200 bg-amber-50 p-8 text-center shadow-soft">
        <p className="font-semibold text-amber-800">Select at least 2 MPs to compare.</p>
        <Link to="/" className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-brand-700 hover:underline">
          ← Browse MPs
        </Link>
      </div>
    );
  }

  const colSpan = mps.length + 1;
  const hasMplads = mps.some((mp) => mp.mplads != null);

  return (
    <div className="animate-fade-up space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 transition hover:text-brand-700"
        >
          <span aria-hidden>←</span> Back
        </button>
        <h1 className="font-display text-xl font-bold text-slate-900">
          Comparing {mps.length} MPs
        </h1>
      </div>

      <div className="overflow-hidden rounded-4xl border border-slate-200/70 bg-white shadow-card">
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="sticky left-0 z-20 min-w-[140px] border-r border-slate-100 bg-slate-50/80 px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Metric
                </th>
                {mps.map((mp) => (
                  <MPHeaderCell key={mp.prs_slug} mp={mp} onRemove={handleRemove} />
                ))}
              </tr>
            </thead>
            <tbody>

              {/* PROFILE */}
              <SectionHeader label="Profile" colSpan={colSpan} />
              <TextRow label="Terms" mps={mps} getValue={(mp) => ordinal(mp.terms)} />
              <TextRow label="Age" mps={mps} getValue={(mp) => mp.age ? `${mp.age} yrs` : null} />
              <TextRow label="Gender" mps={mps} getValue={(mp) => mp.gender} />
              <TextRow label="Education" mps={mps} getValue={(mp) => mp.education} />

              {/* PERFORMANCE SCORES */}
              <SectionHeader label="Performance Scores  (0–100 percentile within peer group)" colSpan={colSpan} />
              <ScoreRow label="Overall" mps={mps} getValue={(mp) => mp.total_score} />
              <ScoreRow label="Attendance" mps={mps} getValue={(mp) => getScore(mp, "attendance_score")} />
              <ScoreRow label="Questions" mps={mps} getValue={(mp) => getScore(mp, "questions_score")} />
              <ScoreRow label="Debates" mps={mps} getValue={(mp) => getScore(mp, "debates_score")} />
              <ScoreRow label="PMBs" mps={mps} getValue={(mp) => getScore(mp, "pmb_score")} />

              {/* RAW STATISTICS */}
              <SectionHeader label="Raw Statistics" colSpan={colSpan} />
              <DataRow
                label="Attendance %"
                mps={mps}
                getValue={(mp) => mp.raw?.attendance_pct}
                higherIsBetter={true}
                format={(v) => `${v.toFixed(1)}%`}
              />
              <DataRow
                label="Questions asked"
                mps={mps}
                getValue={(mp) => mp.raw?.questions_count}
                higherIsBetter={true}
              />
              <DataRow
                label="Debates"
                mps={mps}
                getValue={(mp) => mp.raw?.debates_count}
                higherIsBetter={true}
              />
              <DataRow
                label="PMBs introduced"
                mps={mps}
                getValue={(mp) => mp.raw?.pmb_count}
                higherIsBetter={true}
              />
              <TextRow
                label="Peer group"
                mps={mps}
                getValue={(mp) => mp.peer_group ? `${mp.peer_group} (${mp.total_peers ?? "?"})` : null}
              />

              {/* INTEGRITY */}
              <SectionHeader label="Integrity" colSpan={colSpan} />
              <ScoreRow label="Clean record" mps={mps} getValue={(mp) => mp.clean_record_score} />
              <DataRow
                label="Criminal cases"
                mps={mps}
                getValue={(mp) => mp.criminal_cases}
                higherIsBetter={false}
              />
              <DataRow
                label="Serious cases"
                mps={mps}
                getValue={(mp) => mp.convictions_serious}
                higherIsBetter={false}
              />
              <DataRow
                label="Total assets"
                mps={mps}
                getValue={(mp) => mp.total_assets}
                higherIsBetter={null}
                format={formatINR}
              />
              <DataRow
                label="Asset growth"
                mps={mps}
                getValue={(mp) => mp.asset_growth_pct}
                higherIsBetter={null}
                format={formatPctChange}
              />

              {/* MPLADS */}
              {hasMplads && (
                <>
                  <SectionHeader label="MPLADS Fund" colSpan={colSpan} />
                  <ScoreRow label="MPLADS score" mps={mps} getValue={(mp) => mp.mplads_score} />
                  <DataRow
                    label="Utilization %"
                    mps={mps}
                    getValue={(mp) => mp.mplads?.utilization_pct}
                    higherIsBetter={true}
                    format={(v) => `${v.toFixed(1)}%`}
                  />
                  <DataRow
                    label="Works completed"
                    mps={mps}
                    getValue={(mp) => mp.mplads?.completed_works}
                    higherIsBetter={true}
                  />
                </>
              )}

              {/* STATEMENTS */}
              <SectionHeader label="Public Statements" colSpan={colSpan} />
              <DataRow
                label="Flagged statements"
                mps={mps}
                getValue={(mp) => mp.flagged_count ?? 0}
                higherIsBetter={false}
              />

            </tbody>
          </table>
        </div>
      </div>

      <p className="text-center text-xs text-slate-400">
        N/A = metric not applicable to this MP's role. Scores are 0–100 percentile ranks within peer groups.
        Data sourced from PRS Legislative Research, ADR/MyNeta, and data.gov.in.
      </p>
    </div>
  );
}
