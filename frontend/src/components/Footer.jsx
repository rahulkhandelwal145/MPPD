export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-16 border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6 lg:px-8">

          {/* Left: non-affiliation note */}
          <p className="text-xs text-slate-400">
            © {year} BeforeYouVote · Independent research tool · Not affiliated with any government body or political party ·{" "}
            <span className="text-slate-500">For informational use only</span>
          </p>
          <p className="text-xs text-slate-400">
            Developed by <span className="font-medium text-slate-500">Rahul Khandelwal</span>
          </p>


        </div>
    </footer>
  );
}
