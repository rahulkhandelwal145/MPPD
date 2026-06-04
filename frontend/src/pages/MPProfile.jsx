import { useNavigate, useParams } from "react-router-dom";
import ScoreBar from "../components/ScoreBar";
import ScoreBadge from "../components/ScoreBadge";
import PartyTag from "../components/PartyTag";
import { getRole } from "../components/MPCard";
import IntegritySection from "../components/IntegritySection";
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
    return <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">Loading profile…</div>;
  }

  if (error || !data) {
    return <div className="rounded-3xl border border-red-200 bg-red-50 p-8 shadow-sm">MP profile not found.</div>;
  }

  const { raw, scores, ranks } = data;
  const role = getRole(data);
  const naNote = role ? NA_NOTES[role] : undefined;
  const attendanceNA = role === "Speaker" || role === "LOA";

  return (
    <div className="space-y-6">
      <button onClick={() => navigate(-1)} className="text-sm font-medium text-indigo-600 hover:underline">← Back</button>

      <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-5">
            {data.image_url ? (
              <img
                src={data.image_url}
                alt={data.name}
                className="h-24 w-24 rounded-2xl object-cover flex-shrink-0 border border-slate-200 shadow-sm"
              />
            ) : (
              <div className="h-24 w-24 rounded-2xl bg-slate-100 flex-shrink-0 flex items-center justify-center text-slate-400 text-3xl font-semibold border border-slate-200">
                {data.name.charAt(0)}
              </div>
            )}
            <div>
              <h1 className="text-3xl font-semibold text-slate-950">{data.name}</h1>
              <p className="mt-2 text-sm text-slate-600">{data.constituency}, {data.state}</p>
              {role && (
                <div className="mt-3">
                  <ScoreBadge label={role} />
                </div>
              )}
            </div>
          </div>
          <PartyTag party={data.party} />
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <ScoreBar label="Attendance" value={scores.attendance_score} note={attendanceNA ? naNote : undefined} />
          <ScoreBar label="Questions"  value={scores.questions_score}  note={role ? naNote : undefined} />
          <ScoreBar label="Debates"    value={scores.debates_score}    note={role ? naNote : undefined} />
          <ScoreBar label="PMBs"       value={scores.pmb_score}        note={role ? naNote : undefined} />
        </div>

        <div className="mt-8 rounded-3xl bg-slate-50 p-5">
          <h2 className="text-lg font-semibold text-slate-900">Raw data</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="rounded-3xl border border-slate-200 bg-white p-4">
              <p className="text-sm text-slate-500">Attendance</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">
                {raw.attendance_pct != null ? `${raw.attendance_pct.toFixed(1)}%` : "—"}
              </p>
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

        <IntegritySection slug={slug} />

        <p className="mt-4 text-sm text-slate-500">Data sourced from PRS Legislative Research.</p>
      </div>
    </div>
  );
}
