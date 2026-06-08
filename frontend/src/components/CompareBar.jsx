import { useNavigate } from "react-router-dom";
import { MAX_COMPARE, useCompare } from "../context/CompareContext";

export default function CompareBar() {
  const { selected, removeMP, clearAll } = useCompare();
  const navigate = useNavigate();

  if (!selected.length) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-slate-200 bg-white shadow-[0_-2px_16px_rgba(0,0,0,0.07)]">
      <div className="mx-auto max-w-7xl px-4 py-2.5 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <span className="shrink-0 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Compare ({selected.length}/{MAX_COMPARE})
          </span>
          <div className="flex min-w-0 flex-1 flex-wrap gap-1.5 overflow-hidden">
            {selected.map((mp) => (
              <span key={mp.slug} className="flex items-center gap-1 rounded-full bg-slate-100 pl-1 pr-1.5 py-0.5">
                {mp.image_url ? (
                  <img src={mp.image_url} alt={mp.name} className="h-5 w-5 rounded-full object-cover object-top" />
                ) : (
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-gradient text-[9px] font-bold text-white">
                    {mp.name.charAt(0)}
                  </span>
                )}
                <span className="max-w-[80px] truncate text-xs font-medium text-slate-700">{mp.name}</span>
                <button
                  onClick={() => removeMP(mp.slug)}
                  className="flex h-4 w-4 items-center justify-center rounded-full text-slate-400 hover:bg-slate-200 hover:text-slate-600 transition-colors text-base leading-none"
                  aria-label={`Remove ${mp.name}`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <button
              onClick={clearAll}
              className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
            >
              Clear
            </button>
            <button
              onClick={() => navigate(`/compare?mps=${selected.map((m) => m.slug).join(",")}`)}
              disabled={selected.length < 2}
              className="rounded-full bg-brand-gradient px-4 py-1.5 text-sm font-semibold text-white shadow-soft transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Compare →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
