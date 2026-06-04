function InfoIcon({ note }) {
  return (
    <span className="relative group inline-flex items-center ml-1 cursor-pointer align-middle">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5 text-slate-400 hover:text-slate-600">
        <path fillRule="evenodd" d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0Zm-6 3.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0ZM7.293 5.293a1 1 0 1 1 1.414 1.414L8 7.414V9.5a.75.75 0 0 0 1.5 0V7a1 1 0 0 0-.293-.707l.586-.586V5.293Z" clipRule="evenodd" />
      </svg>
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 rounded-xl bg-slate-800 px-3 py-2 text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-lg">
        {note}
        <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
      </span>
    </span>
  );
}

const NOTE = "Pending allegations declared in the candidate's self-sworn affidavit — these are not convictions.";

export default function CriminalMeter({ totalCases = 0, totalConvictions = 0, convictionsSerious = 0, hasSerious = false, cases = [] }) {
  const count = totalCases || 0;
  const convCount = totalConvictions || 0;
  const convicted = convCount > 0;
  const convSerious = convictionsSerious || 0;
  const convMinor = Math.max(convCount - convSerious, 0);
  // "Truly clean" = no pending cases AND no convictions (only then is the bar green).
  const trulyClean = count <= 0 && !convicted;

  // Bar shows pending (non-convicted) cases only, split by per-case severity.
  // When detail rows are missing but a count exists, fall back to the aggregate flag.
  let seriousN = cases.filter((c) => c.is_serious).length;
  let minorN = cases.filter((c) => !c.is_serious).length;
  if (count > 0 && seriousN + minorN === 0) {
    if (hasSerious) seriousN = 1;
    else minorN = 1;
  }

  return (
    <div className="space-y-3">
      {convicted && (
        <div className="flex items-center gap-3 rounded-2xl bg-slate-900 px-4 py-3 text-white shadow-sm">
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5 flex-shrink-0 text-amber-400" aria-hidden="true">
            <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495ZM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5Zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clipRule="evenodd" />
          </svg>
          <div className="min-w-0">
            <p className="text-sm font-bold uppercase tracking-wide">
              Convicted · {convCount} {convCount === 1 ? "conviction" : "convictions"}
            </p>
            <p className="text-xs text-slate-300">
              <span className={convSerious > 0 ? "font-semibold text-red-300" : ""}>{convSerious} serious</span>
              {" · "}{convMinor} minor
            </p>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between text-sm font-medium text-slate-700">
        <span className="flex items-center">
          Criminal cases
          <InfoIcon note={NOTE} />
        </span>
        {trulyClean && <span className="text-emerald-700">No declared criminal cases</span>}
        {count <= 0 && convicted && <span className="text-slate-500">No pending cases</span>}
      </div>

      {/* Pending (non-convicted) cases: red = serious, yellow = minor */}
      <div className="flex h-3 overflow-hidden rounded-full bg-slate-200">
        {count > 0 ? (
          <>
            {seriousN > 0 && <div className="h-full bg-red-600" style={{ flexGrow: seriousN }} />}
            {minorN > 0 && <div className="h-full bg-yellow-400" style={{ flexGrow: minorN }} />}
          </>
        ) : trulyClean ? (
          <div className="h-full w-full bg-emerald-500" />
        ) : null}
      </div>

      {/* Legend / counts */}
      {count > 0 && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
          {seriousN > 0 && (
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-red-600" /> {seriousN} serious
            </span>
          )}
          {minorN > 0 && (
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-yellow-400" /> {minorN} minor
            </span>
          )}
        </div>
      )}

      {cases.length > 0 && (
        <ul className="mt-2 space-y-2">
          {cases.map((c, i) => (
            <li key={i} className="flex items-start gap-2 rounded-2xl border border-slate-200 bg-white p-3 text-sm">
              <span className={`mt-1.5 h-2 w-2 flex-shrink-0 rounded-full ${c.is_serious ? "bg-red-600" : "bg-yellow-400"}`} />
              <div className="min-w-0">
                {c.ipc_section && <p className="font-medium text-slate-800">{c.ipc_section}</p>}
                {c.description && <p className="text-slate-600">{c.description}</p>}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
