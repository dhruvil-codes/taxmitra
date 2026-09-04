import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { I18nProvider } from "./i18n";
import { DisclaimerBanner, Header } from "./components";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Notice from "./pages/Notice";
import Journey from "./pages/Journey";
import Unsupported from "./pages/Unsupported";
import Scrutiny from "./pages/Scrutiny";
import Upload from "./pages/Upload";
import Start from "./pages/Start";

function AppShell() {
  const { pathname } = useLocation();
  const isLanding = pathname === "/";

  return (
    <>
      {!isLanding && <DisclaimerBanner />}
      {!isLanding && <Header />}
      <main className={isLanding ? undefined : "min-h-[80vh] app-main-shell"}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/guide" element={<Start />} />
          <Route path="/login" element={<Login />} />
          <Route path="/notices" element={<Dashboard />} />
          <Route path="/notices/:id" element={<Notice />} />
          <Route path="/notices/:id/journey" element={<Journey />} />
          <Route path="/notices/:id/scrutiny" element={<Scrutiny />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/notices/:id/unsupported" element={<Unsupported />} />
        </Routes>
      </main>
      {!isLanding && (
        <footer className="app-footer">
          <span><b>त</b> Tax Mitra</span>
          <p>Independent prototype · Fictional data · Not affiliated with or endorsed by the Income Tax Department or Government of India</p>
          <small>AI EXPLAINS → RULES DECIDE → HUMANS APPROVE</small>
        </footer>
      )}
    </>
  );
}

export default function App() {
  return (
    <I18nProvider>
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </I18nProvider>
  );
}
