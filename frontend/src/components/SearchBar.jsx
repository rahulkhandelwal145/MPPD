export default function SearchBar({ value, onChange }) {
  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 text-slate-400">
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" />
        </svg>
      </span>
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search by MP name or constituency…"
        className="w-full rounded-full border border-slate-200/80 bg-white py-3.5 pl-12 pr-5 text-sm text-slate-900 shadow-soft outline-none transition focus:border-brand-400 focus:shadow-glow focus:ring-4 focus:ring-brand-100"
      />
    </div>
  );
}
