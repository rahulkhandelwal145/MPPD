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
    <div className="space-y-8">
      <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-3xl font-semibold text-slate-950">Leaderboard</h1>
        <p className="mt-3 text-slate-600">Top and bottom ranked MPs for each performance metric.</p>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          {METRICS.map((item) => (
            <button
              key={item.value}
              className={`rounded-full px-4 py-2 text-sm font-semibold ${metric === item.value ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-700"}`}
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
