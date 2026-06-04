import { Link } from "react-router-dom";
import PartyTag from "./PartyTag";
import ScoreBar from "./ScoreBar";

const RANK_STYLES = {
  1: "bg-gradient-to-br from-amber-300 to-amber-500 text-white",
  2: "bg-gradient-to-br from-slate-300 to-slate-400 text-white",
  3: "bg-gradient-to-br from-orange-300 to-orange-500 text-white",
};

export default function Leaderboard({ title, metric, mps }) {
  const scoreKey = `${metric}_score`;
  return (
    <div className="rounded-4xl border border-slate-200/70 bg-white p-5 shadow-soft">
      <h3 className="px-1 font-display text-lg font-bold tracking-tight text-slate-900">{title}</h3>
      <div className="mt-4 space-y-2.5">
        {mps?.map((mp, index) => {
          const rank = index + 1;
          return (
            <Link
              key={mp.prs_slug}
              to={`/mp/${mp.prs_slug}`}
              className="block rounded-3xl border border-slate-100 p-4 transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-soft"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl text-sm font-bold tabular-nums ${RANK_STYLES[rank] ?? "bg-slate-100 text-slate-500"}`}>
                    {rank}
                  </span>
                  <p className="truncate font-semibold text-slate-900">{mp.name}</p>
                </div>
                <PartyTag party={mp.party} />
              </div>
              <div className="mt-3">
                <ScoreBar label="Score" value={mp[scoreKey]} />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
