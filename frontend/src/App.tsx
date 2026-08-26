import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { I18nProvider } from "./i18n";
import { DisclaimerBanner, Header } from "./components";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Notice from "./pages/Notice";
import Journey from "./pages/Journey";
import Unsupported from "./pages/Unsupported";

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
          <Route path="/notices/:id/unsupported" element={<Unsupported />} />
        </Routes>
      </main>
      {!isLanding && (
        <footer className="text-center text-[11px] text-stone-400 px-4 py-6">
          Tax Mitra — independent hackathon prototype. All data fictional. Not an official
          Income Tax Department service. AI explains. Rules decide. Humans approve.
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
