import { Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import MPProfile from "./pages/MPProfile";
import ComparePage from "./pages/ComparePage";
import Navbar from "./components/Navbar";
import InfoTabs from "./components/InfoTabs";
import ChatPanel from "./components/ChatPanel";
import Footer from "./components/Footer";
import CompareBar from "./components/CompareBar";
import { CompareProvider, useCompare } from "./context/CompareContext";

function MainContent() {
  const { selected } = useCompare();
  return (
    <>
      <main className={`mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 ${selected.length > 0 ? "pb-20" : ""}`}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/mp/:slug" element={<MPProfile />} />
          <Route path="/compare" element={<ComparePage />} />
        </Routes>
      </main>
      <CompareBar />
    </>
  );
}

export default function App() {
  return (
    <CompareProvider>
      <div className="min-h-screen text-slate-900">
        <Navbar />
        <InfoTabs />
        <MainContent />
        <Footer />
        <ChatPanel />
      </div>
    </CompareProvider>
  );
}
