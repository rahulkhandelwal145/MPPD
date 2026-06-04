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

export default function MPCard({ mp }) {
  const role = getRole(mp);
  const naNote = role ? NA_NOTES[role] : undefined;
  const attendanceNA = role === "Speaker" || role === "LOA";

  return (
    <Link to={`/mp/${mp.prs_slug}`} className="block rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          {mp.image_url ? (
            <img
              src={mp.image_url}
              alt={mp.name}
              className="h-12 w-12 rounded-full object-cover flex-shrink-0 border border-slate-200"
            />
          ) : (
            <div className="h-12 w-12 rounded-full bg-slate-100 flex-shrink-0 flex items-center justify-center text-slate-400 text-lg font-semibold border border-slate-200">
              {mp.name.charAt(0)}
            </div>
          )}
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-slate-900 truncate">{mp.name}</h2>
            <p className="mt-0.5 text-sm text-slate-600">{mp.constituency}, {mp.state}</p>
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

      <div className="mt-4 space-y-3">
        <ScoreBar label="Attendance" value={mp.attendance_score} note={attendanceNA ? naNote : undefined} />
        <ScoreBar label="Questions"  value={mp.questions_score}  note={role ? naNote : undefined} />
        <ScoreBar label="Debates"    value={mp.debates_score}    note={role ? naNote : undefined} />
        <ScoreBar label="PMBs"       value={mp.pmb_score}        note={role ? naNote : undefined} />
      </div>
    </Link>
  );
}
