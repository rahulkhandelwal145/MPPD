import { Link } from "react-router-dom";
import PartyTag from "./PartyTag";
import ScoreBar from "./ScoreBar";
import ScoreBadge from "./ScoreBadge";

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

export default function MPCard({ mp }) {
  const role = getRole(mp);
  const naNote = role ? NA_NOTES[role] : undefined;
  const attendanceNA = role === "Speaker" || role === "LOA";

  return (
    <Link to={`/mp/${mp.prs_slug}`} className="block rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-slate-900 truncate">{mp.name}</h2>
          <p className="mt-1 text-sm text-slate-600">{mp.constituency}, {mp.state}</p>
        </div>
        <PartyTag party={mp.party} />
      </div>

      {role && (
        <div className="mt-3">
          <ScoreBadge label={role} />
        </div>
      )}

      <div className="mt-4 space-y-3">
        <ScoreBar label="Attendance" value={mp.attendance_score} note={attendanceNA ? naNote : undefined} />
        <ScoreBar label="Questions"  value={mp.questions_score}  note={role ? naNote : undefined} />
        <ScoreBar label="Debates"    value={mp.debates_score}    note={role ? naNote : undefined} />
        <ScoreBar label="PMBs"       value={mp.pmb_score}        note={role ? naNote : undefined} />
      </div>
    </Link>
  );
}
