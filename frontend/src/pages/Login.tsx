import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, Citizen, store } from "../lib";
import { Card, PrimaryButton } from "../components";

export default function Login() {
  const { t, locale } = useI18n();
  const navigate = useNavigate();
  const [citizens, setCitizens] = useState<Citizen[] | null>(null);

  useEffect(() => {
    api.citizens().then(setCitizens).catch(() => setCitizens([]));
  }, []);

  const pick = (c: Citizen) => {
    store.setCitizenId(c.id);
    navigate("/notices");
  };

  if (!citizens) return <div className="app-page"><div className="app-loading">LOADING DEMO PROFILES</div></div>;

  return (
    <div className="app-page">
      <p className="app-eyebrow font-semibold tracking-wider text-slate-500">SYNTHETIC DEMO PROFILES</p>
      <h1 className="app-title">{t("login.title")}</h1>
      <p className="app-lead">{t("login.sub")}</p>
      {citizens.length === 0 ? <div className="app-empty mt-8"><p className="app-section-label font-bold text-slate-600">PROFILES UNAVAILABLE</p><p>Demo profiles could not be loaded. Refresh to try again.</p></div> : <div className="app-grid">
        {citizens.map((c) => (
          <Card key={c.id}>
            <p className="app-section-label font-bold text-blue-600">FICTIONAL DEMO PROFILE</p>
            <h2 className="text-2xl font-bold text-slate-900 mt-1">{c.name}</h2>
            <p className="text-sm font-semibold text-slate-700">{c.city} · PAN {c.pan_masked}</p>
            <p className="text-sm text-slate-600 mt-4 leading-relaxed">{c.profile_note?.[locale] ?? c.profile_note?.en}</p>
            <div className="mt-6"><PrimaryButton onClick={() => pick(c)}>{t("login.cta", { name: c.name })} →</PrimaryButton></div>
          </Card>
        ))}
      </div>}
      <p className="app-eyebrow mt-5 font-medium text-slate-500">{t("login.note")}</p>
    </div>
  );
}
