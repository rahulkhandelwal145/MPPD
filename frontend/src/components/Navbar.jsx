import { Link, NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <header className="bg-slate-950 text-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-5 sm:px-6 lg:px-8">
        <Link to="/" className="text-xl font-semibold tracking-tight">
          MP Scorer
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <NavLink to="/" className={({ isActive }) => isActive ? "text-white" : "text-slate-300 hover:text-white"} end>Home</NavLink>
          <NavLink to="/leaderboard" className={({ isActive }) => isActive ? "text-white" : "text-slate-300 hover:text-white"}>Leaderboard</NavLink>
        </nav>
      </div>
    </header>
  );
}
