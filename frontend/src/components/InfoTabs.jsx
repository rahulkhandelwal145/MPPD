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
  { risk: "high",   icon: "🛡️", title: "Limitation of liability — no legal responsibility accepted", body: "This site and its individual operator accept no liability for any direct, indirect, or consequential loss, damage, or legal action arising from use of information here. All data is reproduced in good faith from public-domain sources (ECI affidavits, Parliament records, government open-data portals). This site operates in the public interest under fair dealing provisions of Section 52, Indian Copyright Act 1957. Reproduction of publicly filed documents is a lawful exercise of the right to access information about elected officials in their public capacity." },
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

const ABOUT_CARDS = [
  {
    icon: "🎯",
    title: "Purpose",
    items: [
      "Civic education and research — making scattered public data easier to browse and compare",
      "Aggregates data already published by government bodies, the Election Commission, and independent research organisations",
      "Enables citizens to search, filter, and compare MPs' publicly available parliamentary records in one place",
    ],
  },
  {
    icon: "📊",
    title: "What this site shows",
    items: [
      "Parliamentary participation metrics (attendance, questions, debates, Private Member Bills) from PRS Legislative Research",
      "Criminal cases and asset declarations from self-sworn election affidavits via ADR / MyNeta",
      "MPLADS constituency fund utilisation from data.gov.in",
      "AI-extracted public statements attributed to MPs in major English-language news outlets",
    ],
  },
  {
    icon: "🚫",
    title: "What this site does not do",
    items: [
      "Does not produce original analysis or make editorial judgements about MPs",
      "Does not recommend or influence voting choices",
      "Scores and rankings are mechanical computations on public data — not editorial opinions",
    ],
  },
  {
    icon: "⚠️",
    title: "Known limitations",
    items: [
      "Parliamentary metrics cover only quantitative participation — not constituency service, committee work, or legislation quality",
      "Statement Monitor covers approximately 6 of 543 MPs (15-outlet English whitelist; regional press excluded)",
      "Data reflects the most recent pipeline run and may lag behind the current session",
    ],
  },
  {
    icon: "✉️",
    title: "Corrections & contact",
    items: [
      "If you spot incorrect data or a mismatched MP profile, contact: rdk14592@gmail.com",
      "Public figures or their representatives may request factual corrections via the same address",
      "Operated by an individual developer in a personal, non-commercial capacity",
    ],
  },
];

function AboutPanel() {
  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
        <p className="text-sm font-bold text-amber-900">Independent, non-commercial research tool</p>
        <p className="mt-1 text-xs leading-relaxed text-amber-800">
          Not affiliated with the Parliament of India, the Election Commission, any political party, PRS, ADR, MyNeta, or any government body. Operated by an individual developer in a personal capacity.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {ABOUT_CARDS.map((card) => (
          <div key={card.title} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm font-bold text-slate-900">
              <span className="mr-1.5">{card.icon}</span>{card.title}
            </p>
            <ul className="mt-3 space-y-1.5">
              {card.items.map((item) => (
                <li key={item} className="flex items-start gap-2 text-xs text-slate-500">
                  <span className="mt-1 h-1 w-1 flex-shrink-0 rounded-full bg-slate-300" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
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
