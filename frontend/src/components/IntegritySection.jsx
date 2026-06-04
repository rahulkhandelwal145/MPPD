import useIntegrity from "../hooks/useIntegrity";
import CriminalMeter from "./CriminalMeter";
import AssetsPanel from "./AssetsPanel";

export default function IntegritySection({ slug }) {
  const { loading, data, error, notFound } = useIntegrity(slug);

  if (loading) {
    return (
      <div className="mt-8 rounded-3xl bg-slate-50 p-5 text-slate-600">Loading integrity data…</div>
    );
  }

  if (notFound) {
    return (
      <div className="mt-8 rounded-3xl bg-slate-50 p-5 text-slate-500">
        Integrity data not yet available for this MP.
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mt-8 rounded-3xl border border-red-200 bg-red-50 p-5 text-red-700">
        Unable to load integrity data.
      </div>
    );
  }

  const { criminal, assets, education, disclaimer } = data;

  return (
    <div className="mt-8 rounded-3xl bg-slate-50 p-5">
      <h2 className="text-lg font-semibold text-slate-900">Integrity &amp; Background</h2>

      <div className="mt-4 space-y-6">
        <CriminalMeter
          totalCases={criminal?.total_cases}
          totalConvictions={criminal?.total_convictions}
          convictionsSerious={criminal?.convictions_serious}
          hasSerious={criminal?.has_serious_cases}
          cases={criminal?.cases ?? []}
        />

        <AssetsPanel assets={assets} education={education} />
      </div>

      {disclaimer && <p className="mt-5 text-xs text-slate-500">{disclaimer}</p>}
    </div>
  );
}
