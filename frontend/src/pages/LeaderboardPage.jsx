import { useState } from "react";
import useLeaderboard from "../hooks/useLeaderboard";
import Leaderboard from "../components/Leaderboard";

const METRICS = [
  { label: "Attendance", value: "attendance" },
  { label: "Questions", value: "questions" },
  { label: "Debates", value: "debates" },
  { label: "PMBs", value: "pmb" },
];

export default function LeaderboardPage() {
  const [metric, setMetric] = useState("attendance");
  const top = useLeaderboard(metric, "top", 20);
  const bottom = useLeaderboard(metric, "bottom", 20);

  return (
    <div className="animate-fade-up space-y-8">
      <div className="rounded-4xl border border-slate-200/70 bg-white p-8 shadow-soft">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gradient">Rankings</p>
        <h1 className="mt-2 font-display text-3xl font-extrabold tracking-tight text-slate-950 sm:text-4xl">Leaderboard</h1>
        <p className="mt-2 text-slate-500">Top and bottom ranked MPs for each performance metric.</p>
        <div className="mt-6 flex flex-wrap items-center gap-2">
          {METRICS.map((item) => (
            <button
              key={item.value}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                metric === item.value
                  ? "bg-brand-gradient text-white shadow-glow"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
              onClick={() => setMetric(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Leaderboard title="Top 20" metric={metric} mps={top.data || []} />
        <Leaderboard title="Bottom 20" metric={metric} mps={bottom.data || []} />
      </div>
    </div>
  );
}
