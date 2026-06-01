import { useEffect, useState } from "react";
import MPCard from "../components/MPCard";
import SearchBar from "../components/SearchBar";
import FilterBar from "../components/FilterBar";
import PipelineStatus from "../components/PipelineStatus";
import useMPs from "../hooks/useMPs";
import { fetchParties } from "../lib/api";

export default function Home() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [party, setParty] = useState("");
  const [isMinister, setIsMinister] = useState("");
  const [sort, setSort] = useState("");
  const [direction, setDirection] = useState("desc");
  const [page, setPage] = useState(1);
  const [parties, setParties] = useState([]);

  useEffect(() => {
    const t = setTimeout(() => { setDebouncedQuery(query); setPage(1); }, 300);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    fetchParties().then(setParties).catch(() => {});
  }, []);

  function handlePartyChange(value) { setParty(value); setPage(1); }
  function handleMinisterChange(value) { setIsMinister(value); setPage(1); }
  function handleSortChange(value) { setSort(value); setPage(1); }
  function handleDirectionChange(value) { setDirection(value); setPage(1); }
  const { loading, data, error, summary } = useMPs({
    party: party || undefined,
    is_minister: isMinister === "" ? undefined : isMinister === "true",
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
        <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_300px]">
          <div className="space-y-5">
            <SearchBar value={query} onChange={setQuery} />
            <FilterBar
              party={party}
              onPartyChange={handlePartyChange}
              parties={parties}
              isMinister={isMinister}
              onMinisterChange={handleMinisterChange}
              sort={sort}
              onSortChange={handleSortChange}
              direction={direction}
              onDirectionChange={handleDirectionChange}
            />
          </div>
          <PipelineStatus lastRun={summary} />
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
