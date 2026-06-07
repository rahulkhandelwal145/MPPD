// Election symbol emoji + brand colour for each party.
// Symbols approximate the EC-assigned election symbols.
const PARTIES = {
  // NDA
  "BJP":      { symbol: "🪷", bg: "bg-amber-50",   text: "text-amber-700",   ring: "ring-amber-200"   }, // Lotus
  "TDP":      { symbol: "🚲", bg: "bg-yellow-50",  text: "text-yellow-700",  ring: "ring-yellow-200"  }, // Bicycle
  "JDU":      { symbol: "➡️", bg: "bg-green-50",   text: "text-green-700",   ring: "ring-green-200"   }, // Arrow
  "SHS":      { symbol: "🏹", bg: "bg-orange-50",  text: "text-orange-700",  ring: "ring-orange-200"  }, // Bow & Arrow (Shiv Sena)
  "LJP(RV)":  { symbol: "🦅", bg: "bg-slate-50",   text: "text-slate-700",   ring: "ring-slate-200"   }, // Eagle (bungalow)
  "LJP":      { symbol: "🦅", bg: "bg-slate-50",   text: "text-slate-700",   ring: "ring-slate-200"   },
  "AJSU":     { symbol: "⭐", bg: "bg-amber-50",   text: "text-amber-700",   ring: "ring-amber-200"   },
  "NPP":      { symbol: "📕", bg: "bg-red-50",     text: "text-red-700",     ring: "ring-red-200"     },
  "SKM":      { symbol: "🌻", bg: "bg-yellow-50",  text: "text-yellow-700",  ring: "ring-yellow-200"  },

  // INDIA Alliance
  "INC":      { symbol: "✋", bg: "bg-sky-50",     text: "text-sky-700",     ring: "ring-sky-200"     }, // Hand
  "SP":       { symbol: "🚲", bg: "bg-red-50",     text: "text-red-700",     ring: "ring-red-200"     }, // Bicycle
  "AITC":     { symbol: "🌸", bg: "bg-teal-50",    text: "text-teal-700",    ring: "ring-teal-200"    }, // Jora Ghash Phul
  "TMC":      { symbol: "🌸", bg: "bg-teal-50",    text: "text-teal-700",    ring: "ring-teal-200"    },
  "DMK":      { symbol: "☀️", bg: "bg-orange-50",  text: "text-orange-700",  ring: "ring-orange-200"  }, // Rising Sun
  "SS(UBT)":  { symbol: "🔥", bg: "bg-amber-50",   text: "text-amber-700",   ring: "ring-amber-200"   }, // Flaming Torch
  "NCP(SP)":  { symbol: "📯", bg: "bg-indigo-50",  text: "text-indigo-700",  ring: "ring-indigo-200"  }, // Man blowing turha
  "RJD":      { symbol: "🪔", bg: "bg-emerald-50", text: "text-emerald-700", ring: "ring-emerald-200" }, // Lantern
  "AAP":      { symbol: "🧹", bg: "bg-blue-50",    text: "text-blue-700",    ring: "ring-blue-200"    }, // Broom
  "CPI(M)":   { symbol: "⚒️", bg: "bg-red-100",    text: "text-red-800",     ring: "ring-red-300"     }, // Hammer & Sickle
  "CPIM":     { symbol: "⚒️", bg: "bg-red-100",    text: "text-red-800",     ring: "ring-red-300"     },
  "CPI":      { symbol: "🌾", bg: "bg-red-50",     text: "text-red-700",     ring: "ring-red-200"     }, // Ears of Corn & Sickle
  "JMM":      { symbol: "🏹", bg: "bg-green-50",   text: "text-green-700",   ring: "ring-green-200"   }, // Bow & Arrow
  "VCK":      { symbol: "⭐", bg: "bg-slate-50",   text: "text-slate-700",   ring: "ring-slate-200"   },
  "MDMK":     { symbol: "☀️", bg: "bg-yellow-50",  text: "text-yellow-700",  ring: "ring-yellow-200"  },

  // Others
  "YSRCP":    { symbol: "🌀", bg: "bg-blue-50",    text: "text-blue-700",    ring: "ring-blue-200"    }, // Ceiling Fan
  "BJD":      { symbol: "🐚", bg: "bg-slate-50",   text: "text-slate-700",   ring: "ring-slate-200"   }, // Conch Shell
  "BSP":      { symbol: "🐘", bg: "bg-blue-50",    text: "text-blue-700",    ring: "ring-blue-200"    }, // Elephant
  "NCP":      { symbol: "⏰", bg: "bg-slate-50",   text: "text-slate-700",   ring: "ring-slate-200"   }, // Clock
  "SAD":      { symbol: "⚖️", bg: "bg-slate-50",   text: "text-slate-700",   ring: "ring-slate-200"   }, // Scales
  "AIADMK":   { symbol: "🌅", bg: "bg-orange-50",  text: "text-orange-700",  ring: "ring-orange-200"  }, // Two Leaves
  "TRS":      { symbol: "🚗", bg: "bg-pink-50",    text: "text-pink-700",    ring: "ring-pink-200"    }, // Car
  "BRS":      { symbol: "🚗", bg: "bg-pink-50",    text: "text-pink-700",    ring: "ring-pink-200"    },
  "SDF":      { symbol: "🌿", bg: "bg-green-50",   text: "text-green-700",   ring: "ring-green-200"   },
  "IND":      { symbol: "👤", bg: "bg-slate-50",   text: "text-slate-600",   ring: "ring-slate-200"   }, // Independent
};

const FALLBACK = { symbol: null, bg: "bg-slate-50", text: "text-slate-600", ring: "ring-slate-200" };

export default function PartyTag({ party }) {
  const p = (party && PARTIES[party.toUpperCase()]) || PARTIES[party] || FALLBACK;
  return (
    <span className={`inline-flex flex-shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${p.bg} ${p.text} ${p.ring}`}>
      {p.symbol && <span aria-hidden className="text-[11px] leading-none">{p.symbol}</span>}
      {party || "Unknown"}
    </span>
  );
}
