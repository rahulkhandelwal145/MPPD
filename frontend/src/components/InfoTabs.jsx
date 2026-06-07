import { useState } from "react";
import useFreshness from "../hooks/useFreshness";

// ── helpers ──────────────────────────────────────────────────────────────────

function timeAgo(iso) {
  if (!iso) return null;
  const d = Math.floor((Date.now() - new Date(iso)) / 86400000);
  if (d === 0) return "today";
  if (d === 1) return "yesterday";
  if (d < 7)  return `${d} days ago`;
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

// ── static content ────────────────────────────────────────────────────────────

const SOURCES = [
  {
    id: "prs",
    icon: "🏛️",
    label: "Parliamentary Performance",
    provider: "PRS Legislative Research",
    href: "https://prsindia.org/mptrack",
    items: ["Attendance (all sessions)", "Questions asked", "Debate participation", "Private Member Bills"],
    note: "Independent, non-partisan. May lag behind the current session.",
  },
  {
    id: "integrity",
    icon: "📋",
    label: "Criminal & Asset Declarations",
    provider: "ADR / MyNeta",
    href: "https://myneta.info",
    items: ["Pending criminal cases (self-declared)", "Total assets & liabilities", "Asset history across elections", "Educational qualifications"],
    note: "Figures are self-declared in ECI affidavits — not independently audited.",
  },
  {
    id: "mplads",
    icon: "💰",
    label: "Constituency Funds",
    provider: "MPLADS / data.gov.in",
    href: "https://data.gov.in",
    items: ["MPLADS allocation & utilisation", "Completed vs recommended works", "Payment success rate"],
    note: "Totals may include carry-forward from the 17th Lok Sabha. MP names are fuzzy-matched.",
  },
  {
    id: "statements",
    icon: "📰",
    label: "Public Statements",
    provider: "Google News",
    href: "https://news.google.com",
    items: ["Direct quotes from major English outlets", "AI-extracted and classified", "Flags constitutional / factual concerns"],
    note: "Only ~6 of 543 MPs have regular coverage in the 15-outlet whitelist. Regional press not included.",
  },
];

const DISCLAIMERS = [
  { risk: "high",   icon: "⚖️", title: "Criminal cases are allegations, not convictions",  body: "Declared cases are pending allegations from self-sworn affidavits — not charges, not convictions. Do not infer guilt." },
  { risk: "high",   icon: "📋", title: "Asset figures are self-declared and unaudited",      body: "Asset values come from election affidavits. They are not verified against tax filings or any other record." },
  { risk: "high",   icon: "🤖", title: "AI content may contain errors",                      body: "Statement classifications are produced by an LLM and may be wrong, incomplete, or out of context. Always read the linked source article." },
  { risk: "medium", icon: "📊", title: "Scores are relative percentile rankings",            body: "A score of 5 means median performance within the peer group — not a rating of overall effectiveness as an MP." },
  { risk: "medium", icon: "🕒", title: "Data may be outdated",                               body: "Pipelines run periodically. Data may lag behind the current Lok Sabha session or the latest government publications." },
  { risk: "low",    icon: "🔗", title: "Name matching is imperfect",                         body: "MPLADS and MyNeta records are matched by fuzzy string matching. Low-confidence matches are flagged in the UI." },
];

const RISK_CLS = {
  high:   "border-red-100 bg-red-50/60 text-red-800",
  medium: "border-amber-100 bg-amber-50/60 text-amber-800",
  low:    "border-slate-100 bg-slate-50 text-slate-600",
};

// ── sub-panels ────────────────────────────────────────────────────────────────

function DataPanel({ freshness }) {
  const byId = Object.fromEntries((freshness?.sources ?? []).map((s) => [s.id, s]));

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {SOURCES.map((s) => {
        const f = byId[s.id];
        const ago = f ? timeAgo(f.last_run_at) : null;
        return (
          <div key={s.id} className="flex flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <span className="text-2xl leading-none">{s.icon}</span>
              {ago && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">
                  {ago}
                </span>
              )}
            </div>
            <p className="mt-2 text-sm font-bold text-slate-900">{s.label}</p>
            <a
              href={s.href}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-0.5 text-[11px] font-medium text-indigo-500 hover:underline"
            >
              {s.provider} ↗
            </a>
            {f && (
              <p className="mt-2 text-[11px] font-semibold text-slate-500">
                {f.record_count.toLocaleString("en-IN")} {f.unit}
              </p>
            )}
            <ul className="mt-3 flex-1 space-y-1">
              {s.items.map((item) => (
                <li key={item} className="flex items-start gap-1.5 text-[11px] text-slate-500">
                  <span className="mt-1 h-1 w-1 flex-shrink-0 rounded-full bg-slate-300" />
                  {item}
                </li>
              ))}
            </ul>
            <p className="mt-3 text-[10px] italic leading-relaxed text-slate-400">{s.note}</p>
          </div>
        );
      })}
    </div>
  );
}

function AboutPanel() {
  return (
    <div className="mx-auto max-w-2xl space-y-4 text-sm leading-relaxed text-slate-600">
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
        <p className="font-bold text-amber-900">Independent, non-commercial research tool</p>
        <p className="mt-1">Not affiliated with the Parliament of India, the Election Commission, any political party, PRS, ADR, MyNeta, or any government body.</p>
      </div>
      <p>This tool aggregates publicly available data about Members of Parliament in the 18th Lok Sabha into a single searchable interface. All underlying data is sourced from government bodies, the Election Commission, and independent research organisations.</p>
      <p><span className="font-semibold text-slate-800">Purpose:</span> Civic education and research. To make scattered public data easier to browse and compare.</p>
      <p><span className="font-semibold text-slate-800">Limitations:</span> Performance metrics cover only quantitative participation. Constituency work, committee participation, and legislation quality are not captured.</p>
      <p className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500">
        For informational use only. Nothing here constitutes legal, financial, or political advice. Always consult primary sources.
      </p>
    </div>
  );
}

function DisclaimersPanel() {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {DISCLAIMERS.map((d) => (
        <div key={d.title} className={`rounded-2xl border p-4 ${RISK_CLS[d.risk]}`}>
          <p className="flex items-center gap-2 text-sm font-bold">
            <span>{d.icon}</span>{d.title}
          </p>
          <p className="mt-1.5 text-xs leading-relaxed opacity-80">{d.body}</p>
        </div>
      ))}
    </div>
  );
}

// ── main component ────────────────────────────────────────────────────────────

const TABS = [
  { id: "about",       label: "About" },
  { id: "data",        label: "Data Sources" },
  { id: "disclaimers", label: "Disclaimers" },
];

export default function InfoTabs() {
  const [active, setActive] = useState(null);
  const { data: freshness } = useFreshness();

  const toggle = (id) => setActive((prev) => (prev === id ? null : id));

  return (
    <div className="border-b border-slate-200 bg-white">
      {/* ── Tab strip ── */}
      <div className="mx-auto flex max-w-7xl items-center px-4 sm:px-6 lg:px-8">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => toggle(t.id)}
            className={[
              "relative px-4 py-3 text-sm font-semibold transition-colors",
              active === t.id
                ? "text-indigo-600 after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:rounded-full after:bg-indigo-500 after:content-['']"
                : "text-slate-500 hover:text-slate-800",
            ].join(" ")}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Expanded panel ── */}
      {active && (
        <div className="border-t border-slate-100 bg-slate-50/50">
          <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            {active === "data"        && <DataPanel freshness={freshness} />}
            {active === "about"       && <AboutPanel />}
            {active === "disclaimers" && <DisclaimersPanel />}
          </div>
        </div>
      )}
    </div>
  );
}
