const CRORE = 10_000_000;
const LAKH = 100_000;
const enIN = new Intl.NumberFormat("en-IN");

// Format a rupee value (stored as plain rupees) using Indian numbering.
// null/undefined → "—"; 0 → "₹0"; large values collapse to Cr / Lakh.
export function formatINR(n) {
  if (n == null) return "—";
  if (n === 0) return "₹0";

  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";

  if (abs >= CRORE) {
    return `${sign}₹${(abs / CRORE).toFixed(2)} Cr`;
  }
  if (abs >= LAKH) {
    return `${sign}₹${(abs / LAKH).toFixed(2)} Lakh`;
  }
  return `${sign}₹${enIN.format(abs)}`;
}

// Format a percentage change with an explicit sign, e.g. +85%, -12%.
// Very large jumps collapse to a multiplier (×12) to stay readable.
export function formatPctChange(pct) {
  if (pct == null) return "—";
  const sign = pct > 0 ? "+" : pct < 0 ? "-" : "";
  const abs = Math.abs(pct);
  if (abs >= 1000) return `${sign}${(abs / 100 + 1).toFixed(0)}×`;
  return `${sign}${abs < 10 ? abs.toFixed(1) : Math.round(abs)}%`;
}
