import { Link, NavLink } from "react-router-dom";

function navClass({ isActive }) {
  return [
    "rounded-full px-4 py-1.5 text-sm font-medium transition-colors",
    isActive ? "bg-slate-900 text-white shadow-soft" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
  ].join(" ");
}

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/95 shadow-soft">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6 lg:px-8">
        <Link to="/" className="group flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-brand-gradient text-white shadow-glow transition-transform group-hover:scale-105">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
          </span>
          <span className="flex flex-col leading-none">
            <span className="font-display text-lg font-extrabold tracking-tight text-slate-900">
              Before<span className="text-gradient">YouVote</span>
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">18th Lok Sabha</span>
          </span>
        </Link>
        <nav className="flex items-center gap-1">
          <NavLink to="/" className={navClass} end>Home</NavLink>
          <NavLink to="/leaderboard" className={navClass}>Leaderboard</NavLink>
        </nav>
      </div>
    </header>
  );
}
