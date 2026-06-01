export default function FilterBar({ party, onPartyChange, parties = [], isMinister, onMinisterChange, sort, onSortChange, direction, onDirectionChange }) {
  return (
    <div className="grid gap-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:grid-cols-4">
      <div>
        <label className="block text-sm font-medium text-slate-700">Party</label>
        <select className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900" value={party} onChange={(event) => onPartyChange(event.target.value)}>
          <option value="">All parties</option>
          {parties.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700">Minister</label>
        <select className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900" value={isMinister ?? ""} onChange={(event) => onMinisterChange(event.target.value)}>
          <option value="">All MPs</option>
          <option value="true">Ministers</option>
          <option value="false">Non-ministers</option>
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700">Sort by</label>
        <select className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900" value={sort} onChange={(event) => onSortChange(event.target.value)}>
          <option value="">Name</option>
          <option value="attendance_score">Attendance</option>
          <option value="questions_score">Questions</option>
          <option value="debates_score">Debates</option>
          <option value="pmb_score">PMBs</option>
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700">Direction</label>
        <select className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900" value={direction} onChange={(event) => onDirectionChange(event.target.value)}>
          <option value="desc">Descending</option>
          <option value="asc">Ascending</option>
        </select>
      </div>
    </div>
  );
}
