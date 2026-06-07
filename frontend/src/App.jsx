import { Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import MPProfile from "./pages/MPProfile";
import Navbar from "./components/Navbar";
import ChatPanel from "./components/ChatPanel";
import Footer from "./components/Footer";

export default function App() {
  return (
    <div className="min-h-screen text-slate-900">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/mp/:slug" element={<MPProfile />} />
        </Routes>
      </main>
      <Footer />
      <ChatPanel />
    </div>
  );
}
