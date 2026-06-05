function Select({ label, value, onChange, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700">{label}</label>
      <select
        className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-soft outline-none transition hover:border-slate-300 focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {children}
      </select>
    </div>
  );
}

function ToggleChip({ label, checked, onChange }) {
  return (
    <label className="flex cursor-pointer items-center gap-2">
      <input
        type="checkbox"
        className="h-4 w-4 rounded border-slate-300 accent-indigo-600"
        checked={!!checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span className="text-sm text-slate-700">{label}</span>
    </label>
  );
}

export default function FilterBar({
  party, onPartyChange, parties = [],
  state, onStateChange, states = [],
  role, onRoleChange,
  gender, onGenderChange,
  terms, onTermsChange,
  sort, onSortChange, direction, onDirectionChange,
  hasCriminalCases, onHasCriminalCasesChange,
  hasSeriousCases, onHasSeriousCasesChange,
  convicted, onConvictedChange,
  crorepati, onCrorepatiChange,
  onClear,
}) {
  return (
    <div className="space-y-4 rounded-4xl border border-slate-200/70 bg-white p-5 shadow-soft">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Select label="Party" value={party} onChange={onPartyChange}>
          <option value="">All parties</option>
          {parties.map((p) => <option key={p} value={p}>{p}</option>)}
        </Select>
        <Select label="State" value={state} onChange={onStateChange}>
          <option value="">All states</option>
          {states.map((s) => <option key={s} value={s}>{s}</option>)}
        </Select>
        <Select label="Role" value={role} onChange={onRoleChange}>
          <option value="">All roles</option>
          <option value="backbencher">Backbenchers only</option>
          <option value="minister">Ministers</option>
          <option value="speaker">Speaker</option>
          <option value="loa">Leader of Opposition</option>
        </Select>
        <Select label="Gender" value={gender} onChange={onGenderChange}>
          <option value="">All</option>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
        </Select>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Select label="Terms" value={terms} onChange={onTermsChange}>
          <option value="">All terms</option>
          <option value="1">1st term (first-time)</option>
          <option value="2">2 terms</option>
          <option value="3">3 terms</option>
          <option value="4">4 terms</option>
          <option value="5plus">5+ terms</option>
        </Select>
        <Select label="Sort by" value={sort} onChange={onSortChange}>
          <option value="">Name</option>
          <option value="total_score">Total score</option>
          <option value="attendance_score">Attendance</option>
          <option value="questions_score">Questions</option>
          <option value="debates_score">Debates</option>
          <option value="pmb_score">PMBs</option>
          <option value="total_assets">Total assets</option>
          <option value="total_criminal_cases">Criminal cases</option>
        </Select>
        <Select label="Order" value={direction} onChange={onDirectionChange}>
          <option value="desc">Highest first</option>
          <option value="asc">Lowest first</option>
        </Select>
      </div>

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-slate-100 pt-4">
        <span className="text-sm font-medium text-slate-700">Records:</span>
        <ToggleChip label="Has criminal cases" checked={hasCriminalCases} onChange={onHasCriminalCasesChange} />
        <ToggleChip label="Serious cases" checked={hasSeriousCases} onChange={onHasSeriousCasesChange} />
        <ToggleChip label="Convicted" checked={convicted} onChange={onConvictedChange} />
        <ToggleChip label="Crorepati (₹1 Cr+)" checked={crorepati} onChange={onCrorepatiChange} />
        <button
          type="button"
          onClick={onClear}
          className="ml-auto rounded-2xl border border-slate-200 bg-slate-50 px-4 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
        >
          Clear filters
        </button>
      </div>
    </div>
  );
}
