import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, ResolveResult, verifiedIncomeTaxUrl } from "../lib";
import { Card } from "../components";

export default function Unsupported() {
  const { id } = useParams<{ id: string }>();
  const { t, locale } = useI18n();
  const [refusal, setRefusal] = useState<ResolveResult | null>(null);

  useEffect(() => {
    if (!id) return;
    api.refusal(id).then(setRefusal).catch(() => setRefusal(null));
  }, [id]);

  if (!refusal) return <div className="app-page"><div className="app-loading">CHECKING GUIDED SCOPE</div></div>;

  return (
    <div className="app-page">
      <div className="mb-8">
        <p className="app-eyebrow font-semibold tracking-wider text-slate-500">OUTSIDE GUIDED SCOPE</p>
        <h1 className="app-title">
          {refusal?.headline?.[locale] ?? refusal?.headline?.en ?? t("unsupported.title")}
        </h1>
      </div>

      <div className="refusal-layout">
        <Card>
          <p className="app-section-label font-bold text-slate-700">WHY WE STOP HERE</p>
          <p className="app-body">{refusal?.why?.[locale] ?? refusal?.why?.en ?? "…"}</p>
        </Card>
        {refusal?.official_links && (
          <Card>
            <h2 className="app-section-label font-bold text-slate-700">{t("unsupported.links")}</h2>
            <ul className="official-links">
              {refusal.official_links.map((l) => <li key={l.url}><a href={verifiedIncomeTaxUrl(l.url)} target="_blank" rel="noopener noreferrer">{l.label[locale] ?? l.label.en} ↗</a></li>)}
            </ul>
          </Card>
        )}
        <Card className="app-dots refusal-suggestion">
          <h2 className="app-section-label font-bold text-blue-600">{t("unsupported.suggestionTitle")}</h2>
          <p className="app-body">{refusal?.suggestion?.[locale] ?? refusal?.suggestion?.en ?? "…"}</p>
        </Card>
      </div>
      <Link to="/notices" className="app-back">← {t("back.home")}</Link>
    </div>
  );
}
