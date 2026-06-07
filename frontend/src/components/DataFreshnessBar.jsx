import { useState } from "react";
import useFreshness from "../hooks/useFreshness";
import LegalModal from "./LegalModal";

function timeAgo(isoString) {
  if (!isoString) return null;
  const diff = Date.now() - new Date(isoString).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins  <  2)  return "just now";
  if (mins  < 60)  return `${mins}m ago`;
  if (hours < 24)  return `${hours}h ago`;
  if (days  <  7)  return `${days}d ago`;
  return new Date(isoString).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

const SOURCE_META = {
  prs:        { icon: "📊", short: "Parliament" },
  integrity:  { icon: "⚖️", short: "Integrity" },
  mplads:     { icon: "🏗️", short: "MPLADS" },
  statements: { icon: "💬", short: "Statements" },
};

export default function DataFreshnessBar() {
  const { data, loading } = useFreshness();
  const [modalOpen, setModalOpen] = useState(false);

  if (loading || !data?.sources) return null;

  return (
    <>
      <div className="border-b border-slate-100 bg-slate-50/80">
        <div className="mx-auto flex max-w-7xl items-center gap-x-1 px-4 py-2 sm:px-6 lg:px-8">

          {/* Freshness pills */}
          <div className="flex flex-1 flex-wrap items-center gap-x-5 gap-y-1.5">
            <span className="flex-shrink-0 text-[10px] font-bold uppercase tracking-widest text-slate-300">
              Data
            </span>
            {data.sources.map((s) => {
              const ago = timeAgo(s.last_run_at);
              const meta = SOURCE_META[s.id] ?? { icon: "•", short: s.label };
              return (
                <div key={s.id} className="flex items-center gap-1.5">
                  <span className="text-sm leading-none" aria-hidden>{meta.icon}</span>
                  <span className="text-[11px] font-semibold text-slate-500">{meta.short}</span>
                  <span className="text-[11px] text-slate-300">·</span>
                  {ago ? (
                    <span className="text-[11px] text-slate-400">
                      <span className="font-medium text-slate-500">{ago}</span>
                      {" · "}
                      {s.record_count.toLocaleString("en-IN")} {s.unit}
                    </span>
                  ) : (
                    <span className="text-[11px] text-slate-300">no data</span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Source links + About trigger */}
          <div className="ml-4 flex flex-shrink-0 items-center gap-x-3 text-[11px] text-slate-400">
            <a href="https://prsindia.org" target="_blank" rel="noopener noreferrer" className="transition-colors hover:text-indigo-600 hover:underline">PRS</a>
            <span aria-hidden>·</span>
            <a href="https://myneta.info" target="_blank" rel="noopener noreferrer" className="transition-colors hover:text-indigo-600 hover:underline">ADR / MyNeta</a>
            <span aria-hidden>·</span>
            <a href="https://data.gov.in" target="_blank" rel="noopener noreferrer" className="transition-colors hover:text-indigo-600 hover:underline">data.gov.in</a>
            <span aria-hidden className="text-slate-200">|</span>
            <button
              onClick={() => setModalOpen(true)}
              className="font-semibold text-indigo-500 transition-colors hover:text-indigo-700"
            >
              About &amp; Legal ↗
            </button>
          </div>

        </div>
      </div>

      {modalOpen && <LegalModal onClose={() => setModalOpen(false)} />}
    </>
  );
}
