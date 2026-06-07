import { useState } from "react";
import LegalModal from "./LegalModal";

export default function Footer() {
  const [open, setOpen] = useState(false);
  const year = new Date().getFullYear();

  return (
    <>
      <footer className="mt-16 border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6 lg:px-8">

          {/* Left: non-affiliation note */}
          <p className="text-xs text-slate-400">
            © {year} BeforeYouVote · Independent research tool · Not affiliated with any government body or political party ·{" "}
            <span className="text-slate-500">For informational use only</span>
          </p>

          {/* Right: source links + legal button */}
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400">
            <a href="https://prsindia.org" target="_blank" rel="noopener noreferrer" className="hover:text-indigo-600 hover:underline transition-colors">PRS</a>
            <span aria-hidden>·</span>
            <a href="https://myneta.info" target="_blank" rel="noopener noreferrer" className="hover:text-indigo-600 hover:underline transition-colors">ADR / MyNeta</a>
            <span aria-hidden>·</span>
            <a href="https://data.gov.in" target="_blank" rel="noopener noreferrer" className="hover:text-indigo-600 hover:underline transition-colors">data.gov.in</a>
            <span aria-hidden>·</span>
            <button
              onClick={() => setOpen(true)}
              className="font-medium text-indigo-500 hover:text-indigo-700 transition-colors"
            >
              About &amp; Legal ↗
            </button>
          </div>

        </div>
      </footer>

      {open && <LegalModal onClose={() => setOpen(false)} />}
    </>
  );
}
