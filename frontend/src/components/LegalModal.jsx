import { useEffect, useState } from "react";

const TABS = ["About", "Data Sources", "Disclaimers"];

const ABOUT_CARDS = [
  {
    icon: "🎯",
    title: "Purpose",
    items: [
      "Civic education and research — making scattered public data easier to browse and compare",
      "Aggregates data already published by government bodies, the Election Commission of India, and independent research organisations",
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
      "Does not independently verify or investigate any data beyond what the primary sources publish",
    ],
  },
  {
    icon: "⚠️",
    title: "Known limitations",
    items: [
      "Parliamentary metrics cover only quantitative participation — not constituency service, committee work, or legislation quality",
      "Statement Monitor covers approximately 6 of 543 MPs (15-outlet English whitelist; regional and vernacular press excluded)",
      "Data reflects the most recent pipeline run and may lag behind the current Lok Sabha session",
      "Asset figures are AI-extracted from scanned documents and may contain parsing errors",
    ],
  },
  {
    icon: "✉️",
    title: "Corrections & contact",
    items: [
      "If you spot incorrect data or a mismatched MP profile, contact: rdk14592@gmail.com",
      "Public figures or their representatives may request factual corrections via the same address",
      "This site is operated by an individual developer in a personal capacity for non-commercial civic purposes",
    ],
  },
];

const SOURCES = [
  {
    label: "Parliamentary Performance",
    href: "https://prsindia.org/mptrack",
    source: "PRS Legislative Research",
    icon: "🏛️",
    items: [
      "Attendance records for all 18th Lok Sabha sessions",
      "Questions asked (starred & unstarred)",
      "Participation in debates",
      "Private Member Bills introduced",
    ],
    note: "PRS is an independent, non-partisan research organisation. Data reflects the most recent pipeline run and may lag behind the current session.",
  },
  {
    label: "Criminal & Asset Declarations",
    href: "https://myneta.info",
    source: "ADR / MyNeta",
    icon: "📋",
    items: [
      "Criminal cases declared in the candidate's self-sworn affidavit",
      "Total assets and liabilities at time of election",
      "Asset declarations from prior elections (for growth tracking)",
      "Educational qualifications",
    ],
    note: "Data is sourced from affidavits filed with the Election Commission of India. Figures are self-declared and not independently audited or verified.",
  },
  {
    label: "Constituency Development Funds",
    href: "https://data.gov.in",
    source: "MPLADS / data.gov.in",
    icon: "💰",
    items: [
      "MPLADS fund allocations per constituency",
      "Utilisation percentage",
    ],
    note: "Allocations may include unspent carry-forward from the 17th Lok Sabha, so totals can span more than one term. MP names are matched via fuzzy string matching — low-confidence matches are flagged in the UI.",
  },
  {
    label: "Public Statements",
    href: "https://news.google.com",
    source: "Google News RSS",
    icon: "📰",
    items: [
      "Direct quotes attributed to the MP in major English-language news outlets",
      "Quotes are extracted and classified by an AI model",
      "Only statements from a 15-outlet whitelist of national English outlets are included",
    ],
    note: "Regional-language coverage is not included. Approximately 6 of 543 MPs receive regular coverage from these outlets. Coverage is highly uneven.",
  },
];

const DISCLAIMERS = [
  {
    icon: "🛡️",
    title: "Limitation of liability — no legal responsibility accepted",
    body: "This site and its individual operator accept no liability whatsoever for any direct, indirect, incidental, or consequential loss, damage, legal action, or other consequence arising from the use of, or reliance on, information published here. All data is reproduced in good faith from sources already in the public domain (Election Commission of India affidavits, Parliament of India records, government open-data portals, and independent research organisations). This site operates solely in the public interest for civic education and falls within fair dealing provisions under Section 52 of the Indian Copyright Act, 1957. Nothing on this site is intended to defame, harass, or harm any individual. Any reproduction of publicly filed documents (affidavits, attendance records) is a lawful exercise of the right to access information about elected public officials in their public capacity.",
    risk: "high",
  },
  {
    icon: "⚖️",
    title: "Criminal cases are allegations, not convictions",
    body: "Criminal case data is reproduced directly from candidates' self-sworn affidavits filed with the Election Commission of India. A declared case represents a pending allegation — it does not mean the MP has been charged, tried, or found guilty. Do not infer guilt or character from case counts. The distinction between pending cases and convictions is shown separately throughout the UI.",
    risk: "high",
  },
  {
    icon: "📋",
    title: "Asset figures are self-declared and unaudited",
    body: "Asset and liability values are taken verbatim from election affidavits. They are not independently audited, verified, or cross-checked against income tax filings or any other official record. Figures may not reflect actual net worth. Prior-election asset figures are extracted by an AI model from scanned/HTML documents and may contain transcription or parsing errors.",
    risk: "high",
  },
  {
    icon: "🤖",
    title: "AI-generated content may contain errors",
    body: "Public Statement Monitor entries are extracted and classified by a large-language model (LLaMA 3). Classifications may be incorrect, incomplete, or out of context. The model only flags statements that contradict the Indian Constitution, scientific consensus, or the government's own documented data — political opinions are never flagged. Always read the full linked source article before drawing any conclusion. This feature is explicitly labelled as AI-powered in the UI.",
    risk: "high",
  },
  {
    icon: "📊",
    title: "Scores are relative percentile rankings",
    body: "Performance scores (0–10) are peer-normalised percentile rankings within two groups: ministers and non-ministers, for the 18th Lok Sabha. A score of 5 means median performance within that group. A low score reflects below-average parliamentary participation; it is not a comprehensive measure of an MP's work, constituency service, or political impact. Ministers are excluded from questions, debates, and PMB rankings (those are not their primary role).",
    risk: "medium",
  },
  {
    icon: "🕒",
    title: "Data may be outdated",
    body: "Parliamentary performance data is sourced from PRS Legislative Research and reflects the most recent pipeline run. Pipelines are triggered manually; data may be several sessions behind the current Lok Sabha calendar. MPLADS utilisation figures may be delayed relative to the government's published records.",
    risk: "medium",
  },
  {
    icon: "🔗",
    title: "Name matching is imperfect",
    body: "MPLADS and MyNeta data is matched to MPs via fuzzy string matching on names. Where match confidence is below a threshold, the UI displays a warning. Low-confidence or unmatched MPs are listed at /api/v1/integrity/unmatched. If you notice a mismatch, the underlying data is still accurate — only the attribution to a specific MP profile may be incorrect.",
    risk: "low",
  },
];

function riskBadge(risk) {
  if (risk === "high") return "bg-red-50 text-red-700 border-red-200";
  if (risk === "medium") return "bg-amber-50 text-amber-700 border-amber-200";
  return "bg-slate-50 text-slate-600 border-slate-200";
}

export default function LegalModal({ onClose }) {
  const [tab, setTab] = useState(0);

  useEffect(() => {
    const handler = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center sm:items-center"
      aria-modal="true"
      role="dialog"
      aria-label="About & Legal"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div className="relative z-10 flex h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-t-3xl bg-white shadow-2xl sm:h-[80vh] sm:rounded-3xl">

        {/* Header */}
        <div className="flex flex-shrink-0 items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">Legal & Sources</p>
            <h2 className="mt-0.5 font-display text-lg font-bold text-slate-900">About this site</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex flex-shrink-0 gap-1 border-b border-slate-100 px-6 pt-3">
          {TABS.map((t, i) => (
            <button
              key={t}
              onClick={() => setTab(i)}
              className={`rounded-t-lg px-4 py-2 text-sm font-semibold transition ${
                tab === i
                  ? "border-b-2 border-indigo-500 text-indigo-600"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-6 py-5">

          {/* ─── About ─── */}
          {tab === 0 && (
            <div className="space-y-4">
              {/* Non-affiliation banner */}
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
                <p className="text-sm font-semibold text-amber-900">Independent, non-commercial research tool</p>
                <p className="mt-1 text-xs leading-relaxed text-amber-800">
                  This site is not affiliated with, endorsed by, or associated with the Parliament of
                  India, the Election Commission of India, any political party, PRS Legislative Research,
                  ADR, MyNeta, or any government body. It is an independent civic-information project
                  operated by an individual developer in a personal, non-commercial capacity.
                </p>
              </div>

              {ABOUT_CARDS.map((card) => (
                <div key={card.title} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-900">
                    <span className="mr-1.5">{card.icon}</span>{card.title}
                  </p>
                  <ul className="mt-3 space-y-1.5 text-xs text-slate-600">
                    {card.items.map((item) => (
                      <li key={item} className="flex items-start gap-2">
                        <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-slate-400" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}

              {/* Legal footer notice */}
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs leading-relaxed text-slate-500">
                This site is provided for informational and civic-education purposes only. Nothing on this
                site constitutes legal, financial, or political advice. Data may contain errors. Always
                consult primary sources before relying on any information shown here.
              </div>
            </div>
          )}

          {/* ─── Data Sources ─── */}
          {tab === 1 && (
            <div className="space-y-4">
              {SOURCES.map((s) => (
                <div key={s.label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-900">
                        <span className="mr-1.5">{s.icon}</span>{s.label}
                      </p>
                      <a
                        href={s.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-0.5 inline-block text-xs font-medium text-indigo-600 hover:underline"
                      >
                        {s.source} ↗
                      </a>
                    </div>
                  </div>
                  <ul className="mt-3 space-y-1 text-xs text-slate-600">
                    {s.items.map((item) => (
                      <li key={item} className="flex items-start gap-2">
                        <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-slate-400" />
                        {item}
                      </li>
                    ))}
                  </ul>
                  <p className="mt-3 text-xs leading-relaxed text-slate-500 italic">{s.note}</p>
                </div>
              ))}
            </div>
          )}

          {/* ─── Disclaimers ─── */}
          {tab === 2 && (
            <div className="space-y-3">
              {DISCLAIMERS.map((d) => (
                <div
                  key={d.title}
                  className={`rounded-2xl border p-4 ${riskBadge(d.risk)}`}
                >
                  <p className="text-sm font-semibold">
                    <span className="mr-1.5">{d.icon}</span>{d.title}
                  </p>
                  <p className="mt-1.5 text-xs leading-relaxed opacity-80">{d.body}</p>
                </div>
              ))}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
