import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, ResolveResult } from "../lib";
import { Card } from "../components";

export default function Unsupported() {
  const { id } = useParams<{ id: string }>();
  const { t, locale } = useI18n();
  const [refusal, setRefusal] = useState<ResolveResult | null>(null);

  useEffect(() => {
    if (!id) return;
    api.refusal(id).then(setRefusal).catch(() => setRefusal(null));
  }, [id]);

  return (
    <div className="app-page">
      <div className="mb-8">
        <p className="app-eyebrow">[ OUTSIDE GUIDED SCOPE ]</p>
        <h1 className="app-title">
          {refusal?.headline?.[locale] ?? refusal?.headline?.en ?? t("unsupported.title")}
        </h1>
      </div>

      <Card className="mb-4">
        <p className="text-sm text-stone-700 leading-relaxed">
          {refusal?.why?.[locale] ?? refusal?.why?.en ?? "…"}
        </p>
      </Card>

      {refusal?.official_links && (
        <Card className="mb-4">
          <h2 className="font-bold text-sm uppercase tracking-wide text-stone-500 mb-2">
            {t("unsupported.links")}
          </h2>
          <ul className="space-y-2">
            {refusal.official_links.map((l) => (
              <li key={l.url}>
                <a
                  href={l.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-india-green font-semibold underline text-sm"
                >
                  {l.label[locale] ?? l.label.en} ↗
                </a>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card className="mb-6 app-dots">
        <h2 className="app-section-label">
          {t("unsupported.suggestionTitle")}
        </h2>
        <p className="text-sm text-amber-900 leading-relaxed">
          {refusal?.suggestion?.[locale] ?? refusal?.suggestion?.en ?? "…"}
        </p>
      </Card>

      <Link to="/notices" className="block text-center text-sm text-stone-500 underline">
        ← {t("back.home")}
      </Link>
    </div>
  );
}
