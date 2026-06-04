import { Link } from "react-router-dom";
import PartyTag from "./PartyTag";
import ScoreBar from "./ScoreBar";
import ScoreBadge from "./ScoreBadge";
import { formatINR } from "../lib/format";

const CRORE = 10_000_000;

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
  const vals = [mp.attendance_score, mp.questions_score, mp.debates_score, mp.pmb_score]
    .filter((x) => typeof x === "number");
  if (!vals.length) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

export default function MPCard({ mp }) {
  const role = getRole(mp);
  const naNote = role ? NA_NOTES[role] : undefined;
  const attendanceNA = role === "Speaker" || role === "LOA";

  return (
    <Link
      to={`/mp/${mp.prs_slug}`}
      className="group block h-full rounded-4xl border border-slate-200/70 bg-white p-5 shadow-soft transition-all duration-300 hover:-translate-y-1 hover:border-brand-200 hover:shadow-card"
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
            <h2 className="truncate font-display text-lg font-bold tracking-tight text-slate-900 transition group-hover:text-brand-700">{mp.name}</h2>
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
        </div>
        <span className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-brand-600 opacity-0 transition group-hover:opacity-100">
          View full profile <span aria-hidden>→</span>
        </span>
      </div>
    </Link>
  );
}
