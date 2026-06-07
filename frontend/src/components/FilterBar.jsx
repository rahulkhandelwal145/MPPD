import { useState } from "react";
import { PARTY_ABBR } from "./PartyTag";

function PillSelect({ value, onChange, children, maxW = "max-w-[160px]" }) {
  const active = !!value;
  return (
    <div className="relative flex-shrink-0">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={[
          "cursor-pointer appearance-none rounded-full border py-1.5 pl-3 pr-7 text-sm font-medium outline-none transition",
          active
            ? "border-brand-400 bg-brand-50 text-brand-700"
            : "border-slate-200 bg-white text-slate-600 hover:border-slate-300",
          maxW,
        ].join(" ")}
      >
        {children}
      </select>
      <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-slate-400">▾</span>
    </div>
  );
}

function ActiveChip({ label, onRemove }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700 ring-1 ring-brand-200">
      {label}
      <button type="button" onClick={onRemove} className="ml-0.5 text-brand-400 hover:text-brand-700">×</button>
    </span>
  );
}

function ToggleChip({ label, checked, onChange }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={[
        "rounded-full border px-3 py-1.5 text-xs font-semibold transition",
        checked
          ? "border-brand-400 bg-brand-50 text-brand-700"
          : "border-slate-200 bg-white text-slate-600 hover:border-slate-300",
      ].join(" ")}
    >
      {checked && <span className="mr-1">✓</span>}
      {label}
    </button>
  );
}

function SectionLabel({ children }) {
  return (
    <span className="flex-shrink-0 text-[11px] font-bold uppercase tracking-widest text-slate-400">
      {children}
    </span>
  );
}

export default function FilterBar({
  party, onPartyChange, parties = [],
  state, onStateChange, states = [],
  role, onRoleChange,
  gender, onGenderChange,
  terms, onTermsChange,
  sort, onSortChange,
  direction, onDirectionChange,
  hasCriminalCases, onHasCriminalCasesChange,
  hasSeriousCases, onHasSeriousCasesChange,
  convicted, onConvictedChange,
  crorepati, onCrorepatiChange,
  hasMplads, onHasMpladsChange,
  hasStatements, onHasStatementsChange,
  hasFlagged, onHasFlaggedChange,
  onClear,
}) {
  const [open, setOpen] = useState(false);

  const moreCount = [
    role, gender, terms,
    hasCriminalCases, hasSeriousCases, convicted, crorepati,
    hasMplads, hasStatements, hasFlagged,
  ].filter(Boolean).length;

  const anyActive = !!(party || state || sort || moreCount);

  const activeChips = [
    role === "backbencher" && { label: "Backbenchers", clear: () => onRoleChange("") },
    role === "minister"    && { label: "Ministers",    clear: () => onRoleChange("") },
    role === "speaker"     && { label: "Speaker",      clear: () => onRoleChange("") },
    role === "loa"         && { label: "LOA",          clear: () => onRoleChange("") },
    gender       && { label: gender, clear: () => onGenderChange("") },
    terms        && { label: terms === "5plus" ? "5+ terms" : `${terms} term${terms > 1 ? "s" : ""}`, clear: () => onTermsChange("") },
    hasCriminalCases && { label: "Criminal cases",     clear: () => onHasCriminalCasesChange(false) },
    hasSeriousCases  && { label: "Serious cases",      clear: () => onHasSeriousCasesChange(false) },
    convicted        && { label: "Convicted",          clear: () => onConvictedChange(false) },
    crorepati        && { label: "Crorepati",          clear: () => onCrorepatiChange(false) },
    hasMplads        && { label: "Has MPLADS",         clear: () => onHasMpladsChange(false) },
    hasStatements    && { label: "Has statements",     clear: () => onHasStatementsChange(false) },
    hasFlagged       && { label: "Flagged statements", clear: () => onHasFlaggedChange(false) },
  ].filter(Boolean);

  return (
    <div className="rounded-4xl border border-slate-200/70 bg-white shadow-soft">

      {/* ── Main row ── */}
      <div className="flex flex-wrap items-center gap-3 px-4 py-3">

        {/* Sort group */}
        <div className="flex items-center gap-1.5">
          <SectionLabel>Sort by</SectionLabel>
          <PillSelect value={sort} onChange={onSortChange} maxW="max-w-[150px]">
            <option value="">Name</option>
            <option value="total_score">Total score</option>
            <option value="attendance_score">Attendance</option>
            <option value="questions_score">Questions</option>
            <option value="debates_score">Debates</option>
            <option value="pmb_score">PMBs</option>
            <option value="mplads_score">MPLADS</option>
            <option value="total_assets">Assets</option>
            <option value="total_criminal_cases">Criminal cases</option>
          </PillSelect>
          <button
            type="button"
            onClick={() => onDirectionChange(direction === "desc" ? "asc" : "desc")}
            title={direction === "desc" ? "Highest first" : "Lowest first"}
            className={`flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border text-xs transition ${
              sort
                ? "border-brand-300 bg-brand-50 text-brand-600 hover:bg-brand-100"
                : "border-slate-200 bg-white text-slate-400 hover:border-slate-300 hover:text-slate-600"
            }`}
          >
            {direction === "desc" ? "↓" : "↑"}
          </button>
        </div>

        {/* Divider */}
        <div className="h-5 w-px flex-shrink-0 bg-slate-200" />

        {/* Filter group */}
        <div className="flex flex-wrap items-center gap-1.5">
          <SectionLabel>Filter</SectionLabel>

          <PillSelect value={party} onChange={onPartyChange} maxW="max-w-[120px]">
            <option value="">Party</option>
            {parties.map((p) => (
              <option key={p} value={p}>{PARTY_ABBR[p] || p}</option>
            ))}
          </PillSelect>

          <PillSelect value={state} onChange={onStateChange} maxW="max-w-[120px]">
            <option value="">State</option>
            {states.map((s) => <option key={s} value={s}>{s}</option>)}
          </PillSelect>

          {/* More filters button */}
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className={[
              "flex flex-shrink-0 items-center gap-1.5 rounded-full border py-1.5 pl-3 pr-3 text-sm font-medium transition",
              open || moreCount > 0
                ? "border-brand-400 bg-brand-50 text-brand-700"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300",
            ].join(" ")}
          >
            <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M2 4h12M4 8h8M6 12h4" />
            </svg>
            More
            {moreCount > 0 && (
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-brand-500 text-[10px] font-bold text-white">
                {moreCount}
              </span>
            )}
            <span className="text-[10px] opacity-50">{open ? "▴" : "▾"}</span>
          </button>
        </div>

        {/* Clear — pushed to right edge */}
        {anyActive && (
          <button
            type="button"
            onClick={onClear}
            className="ml-auto flex-shrink-0 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-500 transition hover:border-slate-300 hover:text-slate-700"
          >
            Clear all
          </button>
        )}
      </div>

      {/* ── Active secondary filter chips (collapsed state) ── */}
      {activeChips.length > 0 && !open && (
        <div className="flex flex-wrap gap-1.5 border-t border-slate-100 px-4 pb-3 pt-2">
          {activeChips.map((c) => (
            <ActiveChip key={c.label} label={c.label} onRemove={c.clear} />
          ))}
        </div>
      )}

      {/* ── Expanded "More filters" panel ── */}
      {open && (
        <div className="space-y-3 border-t border-slate-100 px-4 pb-4 pt-3">
          <div className="flex flex-wrap gap-2">
            <PillSelect value={role} onChange={onRoleChange} maxW="max-w-none">
              <option value="">All roles</option>
              <option value="backbencher">Backbenchers only</option>
              <option value="minister">Ministers</option>
              <option value="speaker">Speaker</option>
              <option value="loa">Leader of Opposition</option>
            </PillSelect>
            <PillSelect value={gender} onChange={onGenderChange} maxW="max-w-none">
              <option value="">All genders</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
            </PillSelect>
            <PillSelect value={terms} onChange={onTermsChange} maxW="max-w-none">
              <option value="">All terms</option>
              <option value="1">1st term (first-time)</option>
              <option value="2">2 terms</option>
              <option value="3">3 terms</option>
              <option value="4">4 terms</option>
              <option value="5plus">5+ terms (veteran)</option>
            </PillSelect>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <SectionLabel>Integrity</SectionLabel>
            <ToggleChip label="Has criminal cases" checked={hasCriminalCases} onChange={onHasCriminalCasesChange} />
            <ToggleChip label="Serious cases"      checked={hasSeriousCases}  onChange={onHasSeriousCasesChange} />
            <ToggleChip label="Convicted"          checked={convicted}        onChange={onConvictedChange} />
            <ToggleChip label="Crorepati (₹1 Cr+)" checked={crorepati}        onChange={onCrorepatiChange} />
            <span className="mx-1 h-4 w-px bg-slate-200" />
            <SectionLabel>Data</SectionLabel>
            <ToggleChip label="Has MPLADS"          checked={hasMplads}      onChange={onHasMpladsChange} />
            <ToggleChip label="Has statements"      checked={hasStatements}  onChange={onHasStatementsChange} />
            <ToggleChip label="Flagged statements"  checked={hasFlagged}     onChange={onHasFlaggedChange} />
          </div>
        </div>
      )}
    </div>
  );
}
