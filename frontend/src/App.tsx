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

function AppShell() {
  const { pathname } = useLocation();
  const isLanding = pathname === "/";

  return (
    <>
      {!isLanding && <DisclaimerBanner />}
      {!isLanding && <Header />}
      <main className={isLanding ? undefined : "min-h-[80vh]"}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/guide" element={<Login />} />
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
          <p>Independent prototype · Fictional data · Not an official Income Tax Department service</p>
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
