import { Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import MPProfile from "./pages/MPProfile";
import LeaderboardPage from "./pages/LeaderboardPage";
import Navbar from "./components/Navbar";
import ChatPanel from "./components/ChatPanel";

export default function App() {
  return (
    <div className="min-h-screen text-slate-900">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/mp/:slug" element={<MPProfile />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
        </Routes>
      </main>
      <ChatPanel />
    </div>
  );
}
