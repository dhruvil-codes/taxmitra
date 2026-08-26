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
    <div className="px-4 max-w-md mx-auto py-8">
      <h1 className="text-xl font-extrabold">{t("login.title")}</h1>
      <p className="text-sm text-stone-600 mt-1 mb-5">{t("login.sub")}</p>
      {citizens.map((c) => (
        <Card key={c.id} className="mb-3">
          <p className="font-bold">{c.name}</p>
          <p className="text-sm text-stone-600">{c.city} · PAN {c.pan_masked}</p>
          <p className="text-sm text-stone-500 mt-1">{c.profile_note?.[locale] ?? c.profile_note?.en}</p>
          <div className="mt-4">
            <PrimaryButton onClick={() => pick(c)}>{t("login.cta", { name: c.name })}</PrimaryButton>
          </div>
        </Card>
      ))}
      <p className="text-xs text-stone-400 mt-4">{t("login.note")}</p>
    </div>
  );
}
