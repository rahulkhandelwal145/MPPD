import { useNavigate, useParams } from "react-router-dom";
import ScoreBar from "../components/ScoreBar";
import ScoreBadge from "../components/ScoreBadge";
import PartyTag from "../components/PartyTag";
import useMP from "../hooks/useMP";

export default function MPProfile() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { loading, data, error } = useMP(slug);

  if (loading) {
    return <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">Loading profile…</div>;
  }

  if (error || !data) {
    return <div className="rounded-3xl border border-red-200 bg-red-50 p-8 shadow-sm">MP profile not found.</div>;
  }

  const { raw, scores, ranks } = data;

  return (
    <div className="space-y-6">
      <button onClick={() => navigate(-1)} className="text-sm font-medium text-indigo-600 hover:underline">← Back</button>
      <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-950">{data.name}</h1>
            <p className="mt-2 text-sm text-slate-600">{data.constituency}, {data.state}</p>
          </div>
          <div className="space-y-2 text-right">
            <PartyTag party={data.party} />
            {data.is_minister ? <ScoreBadge label="Minister" /> : null}
            {data.is_speaker ? <ScoreBadge label="Speaker" /> : null}
          </div>
        </div>
        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <ScoreBar label="Attendance" value={scores.attendance_score} />
          <ScoreBar label="Questions" value={scores.questions_score} note={data.is_minister ? "Ministers do not ask questions in their official capacity." : undefined} />
          <ScoreBar label="Debates" value={scores.debates_score} note={data.is_minister ? "Ministers do not participate in this metric." : undefined} />
          <ScoreBar label="PMBs" value={scores.pmb_score} note={data.is_minister ? "Ministers do not sponsor PMBs in this peer comparison." : undefined} />
        </div>
        <div className="mt-8 rounded-3xl bg-slate-50 p-5">
          <h2 className="text-lg font-semibold text-slate-900">Raw data</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="rounded-3xl border border-slate-200 bg-white p-4">
              <p className="text-sm text-slate-500">Attendance</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{raw.attendance_pct != null ? `${raw.attendance_pct}%` : "—"}</p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-white p-4">
              <p className="text-sm text-slate-500">Questions</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{raw.questions_count ?? "—"}</p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-white p-4">
              <p className="text-sm text-slate-500">Debates</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{raw.debates_count ?? "—"}</p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-white p-4">
              <p className="text-sm text-slate-500">PMBs</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{raw.pmb_count ?? "—"}</p>
            </div>
          </div>
        </div>
        <p className="mt-4 text-sm text-slate-500">Data sourced from PRS Legislative Research.</p>
      </div>
    </div>
  );
}
