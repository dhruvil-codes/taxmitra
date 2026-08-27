import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, Citizen, store } from "../lib";
import { Card, PrimaryButton } from "../components";

export default function Login() {
  const { t, locale } = useI18n();
  const navigate = useNavigate();
  const [citizens, setCitizens] = useState<Citizen[]>([]);

  useEffect(() => {
    api.citizens().then(setCitizens).catch(() => setCitizens([]));
  }, []);

  const pick = (c: Citizen) => {
    store.setCitizenId(c.id);
    navigate("/notices");
  };

  return (
    <div className="app-page">
      <p className="app-eyebrow">[ TM / GUIDE / 00 ]</p>
      <h1 className="app-title">{t("login.title")}</h1>
      <p className="app-lead">{t("login.sub")}</p>
      <div className="app-grid">
        {citizens.map((c) => (
          <Card key={c.id}>
            <p className="app-section-label">[ FICTIONAL DEMO PROFILE ]</p>
            <h2 className="text-2xl font-medium">{c.name}</h2>
            <p className="text-sm text-stone-600">{c.city} · PAN {c.pan_masked}</p>
            <p className="text-sm text-stone-500 mt-4 leading-relaxed">{c.profile_note?.[locale] ?? c.profile_note?.en}</p>
            <div className="mt-6"><PrimaryButton onClick={() => pick(c)}>{t("login.cta", { name: c.name })} →</PrimaryButton></div>
          </Card>
        ))}
      </div>
      <p className="app-eyebrow mt-5">{t("login.note")}</p>
    </div>
  );
}
