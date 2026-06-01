import { Link } from "react-router-dom";
import PartyTag from "./PartyTag";
import ScoreBar from "./ScoreBar";

export default function Leaderboard({ title, metric, mps }) {
  const scoreKey = `${metric}_score`;
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      <div className="mt-4 space-y-4">
        {mps?.map((mp, index) => (
          <Link key={mp.prs_slug} to={`/mp/${mp.prs_slug}`} className="block rounded-3xl border border-slate-100 p-4 transition hover:border-indigo-200">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm text-slate-500">#{index + 1}</p>
                <p className="font-semibold text-slate-900">{mp.name}</p>
              </div>
              <PartyTag party={mp.party} />
            </div>
            <div className="mt-3">
              <ScoreBar label="Score" value={mp[scoreKey]} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
