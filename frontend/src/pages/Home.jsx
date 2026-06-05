import { useEffect, useMemo, useRef, useState } from "react";
import MPCard from "../components/MPCard";
import SearchBar from "../components/SearchBar";
import FilterBar from "../components/FilterBar";
import useMPs from "../hooks/useMPs";
import { fetchParties, fetchStates, fetchStatsSummary, fetchIntegritySummary } from "../lib/api";

// Persist the list view (filters/search/sort/page) for this tab so returning
// from an MP profile via Back restores it instead of resetting to defaults.
const FILTERS_KEY = "mpList.filters";

function loadSavedFilters() {
  try {
    return JSON.parse(sessionStorage.getItem(FILTERS_KEY)) || {};
  } catch {
    return {};
  }
}

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

// Terms dropdown value -> exact term count, or a minimum for the "5+" bucket.
function termsParams(terms) {
  if (!terms) return {};
  if (terms === "5plus") return { terms_min: 5 };
  return { terms: Number(terms) };
}

export default function Home() {
  const saved = useMemo(loadSavedFilters, []);
  const [query, setQuery] = useState(saved.query ?? "");
  const [debouncedQuery, setDebouncedQuery] = useState(saved.query ?? "");
  const [party, setParty] = useState(saved.party ?? "");
  const [stateFilter, setStateFilter] = useState(saved.stateFilter ?? "");
  const [gender, setGender] = useState(saved.gender ?? "");
  const [role, setRole] = useState(saved.role ?? "");
  const [terms, setTerms] = useState(saved.terms ?? "");
  const [hasCriminalCases, setHasCriminalCases] = useState(saved.hasCriminalCases ?? false);
  const [hasSeriousCases, setHasSeriousCases] = useState(saved.hasSeriousCases ?? false);
  const [convicted, setConvicted] = useState(saved.convicted ?? false);
  const [crorepati, setCrorepati] = useState(saved.crorepati ?? false);
  const [hasMplads, setHasMplads] = useState(saved.hasMplads ?? false);
  const [sort, setSort] = useState(saved.sort ?? "");
  const [direction, setDirection] = useState(saved.direction ?? "desc");
  const [page, setPage] = useState(saved.page ?? 1);
  const [parties, setParties] = useState([]);
  const [states, setStates] = useState([]);
  const [stats, setStats] = useState(null);
  const [integrity, setIntegrity] = useState(null);

  // Skip the first run so restoring a saved search doesn't reset the saved page.
  const didMount = useRef(false);
  useEffect(() => {
    if (!didMount.current) { didMount.current = true; return; }
    const t = setTimeout(() => { setDebouncedQuery(query); setPage(1); }, 300);
    return () => clearTimeout(t);
  }, [query]);

  // Persist the list view so Back from an MP profile restores it.
  useEffect(() => {
    sessionStorage.setItem(FILTERS_KEY, JSON.stringify({
      query, party, stateFilter, gender, role, terms,
      hasCriminalCases, hasSeriousCases, convicted, crorepati, hasMplads,
      sort, direction, page,
    }));
  }, [query, party, stateFilter, gender, role, terms, hasCriminalCases, hasSeriousCases, convicted, crorepati, hasMplads, sort, direction, page]);

  useEffect(() => {
    fetchParties().then(setParties).catch(() => {});
    fetchStates().then(setStates).catch(() => {});
    fetchStatsSummary().then(setStats).catch(() => {});
    fetchIntegritySummary().then(setIntegrity).catch(() => {});
  }, []);

  // Any filter change resets to page 1.
  const onPage1 = (setter) => (value) => { setter(value); setPage(1); };
  function handleClear() {
    setQuery(""); setParty(""); setStateFilter(""); setGender(""); setRole(""); setTerms("");
    setHasCriminalCases(false); setHasSeriousCases(false); setConvicted(false);
    setCrorepati(false); setHasMplads(false); setSort(""); setDirection("desc"); setPage(1);
  }

  const { loading, data, error } = useMPs({
    party: party || undefined,
    state: stateFilter || undefined,
    gender: gender || undefined,
    ...roleFlags(role),
    ...termsParams(terms),
    has_criminal_cases: hasCriminalCases || undefined,
    has_serious_cases: hasSeriousCases || undefined,
    is_convicted: convicted || undefined,
    is_crorepati: crorepati || undefined,
    has_mplads: hasMplads || undefined,
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
            terms={terms}
            onTermsChange={onPage1(setTerms)}
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
            hasMplads={hasMplads}
            onHasMpladsChange={onPage1(setHasMplads)}
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
            <div className="flex items-center justify-between rounded-4xl border border-slate-200/70 bg-white p-3 pl-5 shadow-soft">
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
