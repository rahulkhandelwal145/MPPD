import { useState } from "react";
import { Link } from "react-router-dom";
import PartyTag from "./PartyTag";
import ScoreBar from "./ScoreBar";
import ScoreBadge from "./ScoreBadge";
import Sparkline from "./Sparkline";
import { formatINR, formatPctChange } from "../lib/format";

const CRORE = 10_000_000;

const yearOf = (s) => s?.match(/(?:19|20)\d{2}/)?.[0];

// Click-to-expand asset trajectory: a growth chip that, when clicked, reveals a
// sparkline + the change since the MP's last and first declarations. Lives
// inside the card's <Link>, so clicks must not trigger navigation.
function AssetTrend({ mp }) {
  const [open, setOpen] = useState(false);
  if (mp.asset_growth_pct == null) return null;

  const up = mp.asset_growth_pct >= 0;
  const chipCls = up ? "bg-amber-100 text-amber-800 hover:bg-amber-200" : "bg-sky-100 text-sky-800 hover:bg-sky-200";
  const lastYear = yearOf(mp.asset_growth_since);
  const firstYear = yearOf(mp.asset_growth_first_since);

  const toggle = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setOpen((v) => !v);
  };

  return (
    <div className="mt-2">
      <button type="button" onClick={toggle} className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold transition ${chipCls}`}>
        {up ? "▲" : "▼"} {formatPctChange(mp.asset_growth_pct)} assets{lastYear ? ` since ${lastYear}` : ""}
        <span className="ml-0.5 text-[10px] opacity-70">{open ? "▴" : "▾"}</span>
      </button>

      {open && (
        <div className="mt-2 rounded-2xl border border-slate-100 bg-slate-50/80 p-3">
          <Sparkline points={mp.asset_series} height={56} />
          <dl className="mt-1 space-y-0.5 text-xs">
            <div className="flex justify-between">
              <dt className="text-slate-500">Since last term{lastYear ? ` (${lastYear})` : ""}</dt>
              <dd className={`font-semibold ${up ? "text-amber-700" : "text-sky-700"}`}>{formatPctChange(mp.asset_growth_pct)}</dd>
            </div>
            {mp.asset_growth_first_pct != null && (
              <div className="flex justify-between">
                <dt className="text-slate-500">Since first term{firstYear ? ` (${firstYear})` : ""}</dt>
                <dd className={`font-semibold ${mp.asset_growth_first_pct >= 0 ? "text-amber-700" : "text-sky-700"}`}>
                  {formatPctChange(mp.asset_growth_first_pct)}
                </dd>
              </div>
            )}
          </dl>
        </div>
      )}
    </div>
  );
}

// Compact integrity chips driven by the list endpoint's affidavit summary.
function IntegrityBadges({ mp }) {
  const chips = [];
  if (mp.convictions > 0) {
    chips.push(["bg-slate-900 text-white", `Convicted${mp.convictions > 1 ? ` ·${mp.convictions}` : ""}`]);
  } else if (mp.has_serious_cases) {
    chips.push(["bg-red-100 text-red-800", "Serious case"]);
  }
  if (mp.criminal_cases > 0 && !(mp.convictions > 0) && !mp.has_serious_cases) {
    chips.push(["bg-yellow-100 text-yellow-800", `${mp.criminal_cases} case${mp.criminal_cases > 1 ? "s" : ""}`]);
  }
  if (mp.total_assets != null) {
    const cls = mp.total_assets >= CRORE ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700";
    chips.push([cls, formatINR(mp.total_assets)]);
  }
  if (chips.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {chips.map(([cls, text], i) => (
        <span key={i} className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${cls}`}>{text}</span>
      ))}
    </div>
  );
}

export function getRole(mp) {
  if (mp.is_speaker)  return "Speaker";
  if (mp.is_loa)      return "LOA";
  if (mp.is_minister) return "Minister";
  return null;
}

const NA_NOTES = {
  Minister: "Not applicable — ministers represent the govt in debates.",
  Speaker:  "Not applicable — the Speaker does not participate in debates.",
  LOA:      "Not applicable — the Leader of Opposition does not sign registers.",
};

function ordinal(n) {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function ringColor(v) {
  if (v == null) return "#cbd5e1";
  if (v >= 67) return "#059669"; // emerald
  if (v >= 34) return "#d97706"; // amber
  return "#e11d48"; // rose
}

// Small donut showing the MP's overall (mean of available) score.
function ScoreRing({ value }) {
  const v = typeof value === "number" ? value : null;
  const r = 20;
  const c = 2 * Math.PI * r;
  const pct = Math.min(Math.max(v ?? 0, 0), 100);
  const color = ringColor(v);
  return (
    <div className="relative h-14 w-14 flex-shrink-0">
      <svg viewBox="0 0 48 48" className="h-14 w-14 -rotate-90">
        <circle cx="24" cy="24" r={r} fill="none" stroke="#eef2f7" strokeWidth="5" />
        <circle
          cx="24" cy="24" r={r} fill="none" stroke={color} strokeWidth="5" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c - (pct / 100) * c}
          style={{ transition: "stroke-dashoffset 0.7s ease" }}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center font-display text-sm font-extrabold tabular-nums" style={{ color }}>
        {v == null ? "—" : Math.round(v)}
      </span>
    </div>
  );
}

function overallScore(mp) {
  // Backend provides total_score (mean of available metrics incl. clean record);
  // fall back to computing it client-side for endpoints that don't (e.g. leaderboard).
  if (typeof mp.total_score === "number") return mp.total_score;
  const vals = [mp.attendance_score, mp.questions_score, mp.debates_score, mp.pmb_score, mp.clean_record_score]
    .filter((x) => typeof x === "number");
  if (!vals.length) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

const CLEAN_RECORD_NOTE =
  "Starts at 100. Each conviction deducts points — major −50, minor −20 (smaller from the 4th on). Floored at 0; pending cases don't count.";

export default function MPCard({ mp }) {
  const role = getRole(mp);
  const naNote = role ? NA_NOTES[role] : undefined;
  const attendanceNA = role === "Speaker" || role === "LOA";

  return (
    <Link
      to={`/mp/${mp.prs_slug}`}
      className="group block h-full rounded-4xl border border-slate-200/70 bg-white p-5 shadow-soft transition-[box-shadow,border-color] duration-200 hover:border-brand-200 hover:shadow-card"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          {mp.image_url ? (
            <img
              src={mp.image_url}
              alt={mp.name}
              className="h-14 w-14 flex-shrink-0 rounded-2xl object-cover object-top ring-2 ring-slate-100 transition group-hover:ring-brand-200"
            />
          ) : (
            <div className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-2xl bg-brand-gradient text-lg font-bold text-white shadow-soft">
              {mp.name.charAt(0)}
            </div>
          )}
          <div className="min-w-0">
            <h2 className="line-clamp-2 font-display text-lg font-bold leading-tight tracking-tight text-slate-900 transition group-hover:text-brand-700">{mp.name}</h2>
            <p className="mt-0.5 truncate text-sm text-slate-500">{mp.constituency}, {mp.state}</p>
          </div>
        </div>
        <PartyTag party={mp.party} />
      </div>

      {(mp.terms || mp.gender || mp.education) && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {mp.terms && (
            <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
              {ordinal(mp.terms)} term
            </span>
          )}
          {mp.gender && (
            <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
              {mp.gender}
            </span>
          )}
          {mp.education && (
            <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full truncate max-w-[12rem]" title={mp.education}>
              {mp.education}
            </span>
          )}
        </div>
      )}

      {role && (
        <div className="mt-3">
          <ScoreBadge label={role} />
        </div>
      )}

      <IntegrityBadges mp={mp} />
      <AssetTrend mp={mp} />

      <div className="mt-4 border-t border-slate-100 pt-4">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Overall score</p>
            <p className="font-display text-xs text-slate-400">mean of tracked metrics</p>
          </div>
          <ScoreRing value={overallScore(mp)} />
        </div>
        <div className="space-y-2.5">
          <ScoreBar label="Attendance" value={mp.attendance_score} note={attendanceNA ? naNote : undefined} />
          <ScoreBar label="Questions"  value={mp.questions_score}  note={role ? naNote : undefined} />
          <ScoreBar label="Debates"    value={mp.debates_score}    note={role ? naNote : undefined} />
          <ScoreBar label="PMBs"       value={mp.pmb_score}        note={role ? naNote : undefined} />
          {mp.clean_record_score != null && (
            <ScoreBar label="Clean record" value={mp.clean_record_score} note={CLEAN_RECORD_NOTE} />
          )}
        </div>
        <span className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-brand-600 opacity-0 transition group-hover:opacity-100">
          View full profile <span aria-hidden>→</span>
        </span>
      </div>
    </Link>
  );
}
