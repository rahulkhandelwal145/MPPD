import { Link } from "react-router-dom";
import PartyTag from "./PartyTag";
import ScoreBar from "./ScoreBar";
import ScoreBadge from "./ScoreBadge";

export default function MPCard({ mp }) {
  return (
    <Link to={`/mp/${mp.prs_slug}`} className="block rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{mp.name}</h2>
          <p className="mt-1 text-sm text-slate-600">{mp.constituency}, {mp.state}</p>
        </div>
        <PartyTag party={mp.party} />
      </div>
      <div className="mt-4 space-y-3">
        <ScoreBar label="Attendance" value={mp.attendance_score} />
        <ScoreBar label="Questions" value={mp.questions_score} note={mp.is_minister ? "Ministers are excluded from this metric." : undefined} />
        <ScoreBar label="Debates" value={mp.debates_score} note={mp.is_minister ? "Ministers are excluded from this metric." : undefined} />
        <ScoreBar label="PMBs" value={mp.pmb_score} note={mp.is_minister ? "Ministers are excluded from this metric." : undefined} />
      </div>
      {mp.is_minister ? <div className="mt-4"><ScoreBadge label="Minister" /></div> : null}
    </Link>
  );
}
