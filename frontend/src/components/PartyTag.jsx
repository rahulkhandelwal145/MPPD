const PARTY_COLORS = {
  BJP: "bg-amber-50 text-amber-700 ring-amber-200",
  INC: "bg-sky-50 text-sky-700 ring-sky-200",
};

export default function PartyTag({ party }) {
  const classes = PARTY_COLORS[party] ?? "bg-slate-50 text-slate-600 ring-slate-200";
  return (
    <span className={`inline-flex flex-shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${classes}`}>
      {party || "Unknown"}
    </span>
  );
}
