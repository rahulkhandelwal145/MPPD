const PARTY_COLORS = {
  BJP: "bg-amber-100 text-amber-700",
  INC: "bg-sky-100 text-sky-700",
};

export default function PartyTag({ party }) {
  const classes = PARTY_COLORS[party] ?? "bg-slate-100 text-slate-700";
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ${classes}`}>{party || "Unknown"}</span>;
}
