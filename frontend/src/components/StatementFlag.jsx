// Category badge for a classified statement. Colour is keyed off the group
// letter (A/B/C/D); the emoji + label come from the category code.
const GROUP_STYLES = {
  A: { dot: "🔴", bg: "bg-red-50",    text: "text-red-700",    ring: "ring-red-200" },
  B: { dot: "🟠", bg: "bg-orange-50", text: "text-orange-700", ring: "ring-orange-200" },
  C: { dot: "🟡", bg: "bg-amber-50",  text: "text-amber-700",  ring: "ring-amber-200" },
  D: { dot: "🟢", bg: "bg-green-50",  text: "text-green-700",  ring: "ring-green-200" },
};

export default function StatementFlag({ category, label }) {
  const group = category?.[0];
  const s = GROUP_STYLES[group] ?? GROUP_STYLES.D;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ring-1 ${s.bg} ${s.text} ${s.ring}`}
    >
      <span aria-hidden>{s.dot}</span>
      {category} — {label}
    </span>
  );
}
