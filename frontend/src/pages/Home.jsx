import { useEffect, useState } from "react";
import MPCard from "../components/MPCard";
import SearchBar from "../components/SearchBar";
import FilterBar from "../components/FilterBar";
import useMPs from "../hooks/useMPs";
import { fetchParties, fetchStates, fetchStatsSummary, fetchIntegritySummary } from "../lib/api";

// Role dropdown value -> minister/speaker/loa flags sent to the API.
function roleFlags(role) {
  switch (role) {
    case "backbencher": return { is_minister: false, is_speaker: false, is_loa: false };
    case "minister": return { is_minister: true };
    case "speaker": return { is_speaker: true };
    case "loa": return { is_loa: true };
    default: return {};
  }
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [party, setParty] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [gender, setGender] = useState("");
  const [role, setRole] = useState("");
  const [hasCriminalCases, setHasCriminalCases] = useState(false);
  const [hasSeriousCases, setHasSeriousCases] = useState(false);
  const [convicted, setConvicted] = useState(false);
  const [crorepati, setCrorepati] = useState(false);
  const [sort, setSort] = useState("");
  const [direction, setDirection] = useState("desc");
  const [page, setPage] = useState(1);
  const [parties, setParties] = useState([]);
  const [states, setStates] = useState([]);
  const [stats, setStats] = useState(null);
  const [integrity, setIntegrity] = useState(null);

  useEffect(() => {
    const t = setTimeout(() => { setDebouncedQuery(query); setPage(1); }, 300);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    fetchParties().then(setParties).catch(() => {});
    fetchStates().then(setStates).catch(() => {});
    fetchStatsSummary().then(setStats).catch(() => {});
    fetchIntegritySummary().then(setIntegrity).catch(() => {});
  }, []);

  // Any filter change resets to page 1.
  const onPage1 = (setter) => (value) => { setter(value); setPage(1); };
  function handleClear() {
    setQuery(""); setParty(""); setStateFilter(""); setGender(""); setRole("");
    setHasCriminalCases(false); setHasSeriousCases(false); setConvicted(false);
    setCrorepati(false); setSort(""); setDirection("desc"); setPage(1);
  }

  const { loading, data, error } = useMPs({
    party: party || undefined,
    state: stateFilter || undefined,
    gender: gender || undefined,
    ...roleFlags(role),
    has_criminal_cases: hasCriminalCases || undefined,
    has_serious_cases: hasSeriousCases || undefined,
    is_convicted: convicted || undefined,
    is_crorepati: crorepati || undefined,
    search: debouncedQuery || undefined,
    sort: sort || undefined,
    direction,
    page,
    limit: 20,
  });

  const mps = data?.results ?? [];

  const heroStats = [
    { label: "MPs tracked", value: stats?.total_mps },
    { label: "With criminal cases", value: integrity?.total_with_cases },
    { label: "Convicted", value: integrity?.total_convicted },
    { label: "Crorepatis", value: integrity?.total_crorepati },
  ];

  return (
    <div className="space-y-8">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-4xl bg-brand-gradient p-8 text-white shadow-lift sm:p-12">
        <div className="pointer-events-none absolute -right-16 -top-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 -left-10 h-72 w-72 rounded-full bg-fuchsia-300/20 blur-3xl" />
        <div className="relative">
          <p className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ring-1 ring-white/20 backdrop-blur">
            18th Lok Sabha · Performance & Integrity
          </p>
          <h1 className="mt-5 max-w-3xl font-display text-4xl font-extrabold leading-[1.05] tracking-tight sm:text-5xl">
            Know your representatives.
            <span className="block text-white/80">Performance, assets & criminal records — in one place.</span>
          </h1>
          <p className="mt-4 max-w-2xl text-base text-white/80">
            Attendance, debates and questions from PRS Legislative Research, combined with self-sworn election affidavits via ADR / MyNeta.
          </p>
          <dl className="mt-8 grid max-w-2xl grid-cols-2 gap-3 sm:grid-cols-4">
            {heroStats.map((s) => (
              <div key={s.label} className="rounded-2xl bg-white/10 px-4 py-3 ring-1 ring-white/15 backdrop-blur">
                <dt className="text-[11px] font-medium uppercase tracking-wide text-white/70">{s.label}</dt>
                <dd className="mt-1 font-display text-2xl font-bold tabular-nums">{s.value ?? "—"}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* Search + filters */}
      <div className="space-y-5">
          <SearchBar value={query} onChange={setQuery} />
          <FilterBar
            party={party}
            onPartyChange={onPage1(setParty)}
            parties={parties}
            state={stateFilter}
            onStateChange={onPage1(setStateFilter)}
            states={states}
            role={role}
            onRoleChange={onPage1(setRole)}
            gender={gender}
            onGenderChange={onPage1(setGender)}
            sort={sort}
            onSortChange={onPage1(setSort)}
            direction={direction}
            onDirectionChange={onPage1(setDirection)}
            hasCriminalCases={hasCriminalCases}
            onHasCriminalCasesChange={onPage1(setHasCriminalCases)}
            hasSeriousCases={hasSeriousCases}
            onHasSeriousCasesChange={onPage1(setHasSeriousCases)}
            convicted={convicted}
            onConvictedChange={onPage1(setConvicted)}
            crorepati={crorepati}
            onCrorepatiChange={onPage1(setCrorepati)}
            onClear={handleClear}
          />
      </div>

      <div className="space-y-5">
        {loading ? (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-4xl border border-slate-200/70 bg-white p-5 shadow-soft">
                <div className="flex items-center gap-3">
                  <div className="skeleton h-12 w-12 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <div className="skeleton h-4 w-2/3 rounded" />
                    <div className="skeleton h-3 w-1/2 rounded" />
                  </div>
                </div>
                <div className="mt-5 space-y-3">
                  {Array.from({ length: 4 }).map((__, j) => <div key={j} className="skeleton h-3 w-full rounded" />)}
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="rounded-4xl border border-red-200 bg-red-50 p-8 text-red-700 shadow-soft">Unable to load MPs.</div>
        ) : mps.length === 0 ? (
          <div className="rounded-4xl border border-slate-200 bg-white p-12 text-center shadow-soft">
            <p className="font-display text-lg font-semibold text-slate-800">No MPs match these filters</p>
            <p className="mt-1 text-sm text-slate-500">Try clearing a filter or adjusting your search.</p>
            <button onClick={handleClear} className="mt-5 rounded-full bg-slate-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-slate-700">Clear filters</button>
          </div>
        ) : (
          <>
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {mps.map((mp, i) => (
                <div key={mp.prs_slug} className="animate-fade-up" style={{ animationDelay: `${Math.min(i, 8) * 40}ms` }}>
                  <MPCard mp={mp} />
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between rounded-4xl border border-slate-200/70 bg-white/80 p-3 pl-5 shadow-soft backdrop-blur">
              <span className="text-sm text-slate-600">
                Showing <span className="font-semibold text-slate-900">{mps.length}</span> of <span className="font-semibold text-slate-900">{data?.total ?? 0}</span> MPs
              </span>
              <div className="flex items-center gap-2">
                <button className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40" onClick={() => setPage((prev) => Math.max(prev - 1, 1))} disabled={page === 1}>← Prev</button>
                <span className="px-1 text-sm font-medium text-slate-500">Page {page}</span>
                <button className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40" onClick={() => setPage((prev) => prev + 1)} disabled={data && page * 20 >= (data.total ?? 0)}>Next →</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
