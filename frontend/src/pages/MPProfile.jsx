import { useNavigate, useParams } from "react-router-dom";
import ScoreBar from "../components/ScoreBar";
import ScoreBadge from "../components/ScoreBadge";
import PartyTag from "../components/PartyTag";
import PartySymbol from "../components/PartySymbol";
import { getRole } from "../components/MPCard";
import IntegritySection from "../components/IntegritySection";
import StatementMonitor from "../components/StatementMonitor";
import MpladsPanel from "../components/MpladsPanel";
import useMP from "../hooks/useMP";

const NA_NOTES = {
  Minister: "Ministers represent the government in debates and do not ask questions or sponsor PMBs in this peer comparison.",
  Speaker:  "The Speaker does not sign the attendance register or participate in debates and questions.",
  LOA:      "The Leader of Opposition does not sign the attendance register.",
};

export default function MPProfile() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { loading, data, error } = useMP(slug);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-48 rounded-4xl" />
        <div className="skeleton h-64 rounded-4xl" />
      </div>
    );
  }

  if (error || !data) {
    return <div className="rounded-4xl border border-red-200 bg-red-50 p-8 text-red-700 shadow-soft">MP profile not found.</div>;
  }

  const { raw, scores } = data;
  const role = getRole(data);
  const naNote = role ? NA_NOTES[role] : undefined;
  const attendanceNA = role === "Speaker" || role === "LOA";

  const rawStats = [
    { label: "Attendance", value: raw.attendance_pct != null ? `${raw.attendance_pct.toFixed(1)}%` : "—" },
    { label: "Questions", value: raw.questions_count ?? "—" },
    { label: "Debates", value: raw.debates_count ?? "—" },
    { label: "PMBs", value: raw.pmb_count ?? "—" },
  ];

  return (
    <div className="animate-fade-up space-y-6">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 transition hover:text-brand-700"
      >
        <span aria-hidden>←</span> Back
      </button>

      {/* Header banner */}
      <div className="overflow-hidden rounded-4xl border border-slate-200/70 bg-white shadow-card">
        <div className="relative h-28 bg-brand-gradient sm:h-32">
          <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
        </div>
        <div className="relative z-10 px-6 pb-6 sm:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex items-end gap-5">
              {data.image_url ? (
                <img
                  src={data.image_url}
                  alt={data.name}
                  className="-mt-12 h-28 w-28 flex-shrink-0 rounded-3xl object-cover object-top ring-4 ring-white shadow-card sm:-mt-14"
                />
              ) : (
                <div className="-mt-12 flex h-28 w-28 flex-shrink-0 items-center justify-center rounded-3xl bg-slate-900 text-4xl font-bold text-white ring-4 ring-white shadow-card sm:-mt-14">
                  {data.name.charAt(0)}
                </div>
              )}
              <div className="pb-1">
                <h1 className="font-display text-3xl font-extrabold tracking-tight text-slate-950">{data.name}</h1>
                <p className="mt-1 text-sm text-slate-500">{data.constituency}, {data.state}</p>
                {role && <div className="mt-3"><ScoreBadge label={role} /></div>}
              </div>
            </div>
            <div className="flex flex-col items-end gap-2 pb-1">
              <PartySymbol party={data.party} size="h-14 w-14" />
              <PartyTag party={data.party} />
              {data.party && (
                <p className="max-w-[180px] text-right text-xs text-slate-400">{data.party}</p>
              )}
            </div>
          </div>

          <div className="mt-8 grid gap-x-8 gap-y-5 lg:grid-cols-2">
            <ScoreBar label="Attendance" value={scores.attendance_score} note={attendanceNA ? naNote : undefined} />
            <ScoreBar label="Questions"  value={scores.questions_score}  note={role ? naNote : undefined} />
            <ScoreBar label="Debates"    value={scores.debates_score}    note={role ? naNote : undefined} />
            <ScoreBar label="PMBs"       value={scores.pmb_score}        note={role ? naNote : undefined} />
          </div>

          <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {rawStats.map((s) => (
              <div key={s.label} className="rounded-3xl border border-slate-200/70 bg-slate-50/70 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{s.label}</p>
                <p className="mt-1.5 font-display text-2xl font-bold text-slate-900 tabular-nums">{s.value}</p>
              </div>
            ))}
          </div>

          <MpladsPanel mplads={data.mplads} />

          <IntegritySection slug={slug} />

          <StatementMonitor slug={slug} />

          <p className="mt-5 text-xs text-slate-400">Performance data sourced from PRS Legislative Research.</p>
        </div>
      </div>
    </div>
  );
}
