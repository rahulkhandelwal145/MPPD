import { useEffect, useState } from "react";
import MPCard from "../components/MPCard";
import SearchBar from "../components/SearchBar";
import FilterBar from "../components/FilterBar";
import useMPs from "../hooks/useMPs";
import { fetchParties, fetchStates } from "../lib/api";

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

  useEffect(() => {
    const t = setTimeout(() => { setDebouncedQuery(query); setPage(1); }, 300);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    fetchParties().then(setParties).catch(() => {});
    fetchStates().then(setStates).catch(() => {});
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

  return (
    <div className="space-y-8">
      <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm uppercase tracking-[0.24em] text-indigo-600">18th Lok Sabha Performance Tracker</p>
        <h1 className="mt-3 text-3xl font-semibold text-slate-950 sm:text-4xl">Scores based on PRS Legislative Research data.</h1>
        <p className="mt-4 max-w-2xl text-slate-600">Updated after every parliamentary session.</p>
        <div className="mt-6 space-y-5">
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
      </div>

      <div className="space-y-4">
        {loading ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-8 text-slate-600 shadow-sm">Loading MPs…</div>
        ) : error ? (
          <div className="rounded-3xl border border-red-200 bg-red-50 p-8 text-red-700 shadow-sm">Unable to load MPs.</div>
        ) : (
          <>
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {mps.map((mp) => (
                <MPCard key={mp.prs_slug} mp={mp} />
              ))}
            </div>
            <div className="flex items-center justify-between rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
              <span className="text-sm text-slate-600">Showing {mps.length} of {data?.total ?? 0} MPs</span>
              <div className="flex items-center gap-2">
                <button className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm" onClick={() => setPage((prev) => Math.max(prev - 1, 1))} disabled={page === 1}>Previous</button>
                <span className="text-sm text-slate-700">Page {page}</span>
                <button className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm" onClick={() => setPage((prev) => prev + 1)} disabled={data && page * 20 >= (data.total ?? 0)}>Next</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
