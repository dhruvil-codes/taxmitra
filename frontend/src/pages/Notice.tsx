import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, Explanation, NoticeCard as NoticeCardT } from "../lib";
import { Card, CitationChips, SavedGuidanceBadge, Stepper } from "../components";

export default function Notice() {
  const { id } = useParams<{ id: string }>();
  const { t, locale } = useI18n();
  const [notice, setNotice] = useState<NoticeCardT | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [error, setError] = useState(false);
  const [showOfficial, setShowOfficial] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.notice(id).then(setNotice).catch(() => setError(true));
    api.explanation(id, locale).then(setExplanation).catch(() => setExplanation(null));
  }, [id, locale]);

  if (error) return <p className="p-6 text-center text-stone-500">Notice not found.</p>;
  if (!notice) return <p className="p-6 text-center text-stone-500">…</p>;

  return (
    <div className="app-page">
      <p className="app-eyebrow">[ TM / NOTICE / 01 ]</p>
      <h1 className="app-title">{notice.title[locale] ?? notice.title.en}</h1>
      <Stepper current={0} />
      <h2 className="text-2xl font-medium leading-snug mb-1">{t("notice.plain")}</h2>
      <p className="text-sm text-stone-500 mb-4">
        {notice.section} · AY {notice.assessment_year}
      </p>

      <div className="mb-3">
        <SavedGuidanceBadge show={explanation?.demo_mode || explanation?.source === "static"} />
      </div>

      <Card className="mb-4 app-dots">
        <p className="app-section-label">[ IN PLAIN LANGUAGE ]</p>
        <p className="text-stone-700 leading-relaxed">
          {explanation?.content.plain_language ?? "…"}
        </p>
        <div className="mt-4 bg-stone-50 border border-stone-200 p-3.5">
          <p className="text-xs font-bold text-amber-800 uppercase tracking-wide mb-1">
            {t("notice.notMean")}
          </p>
          <p className="text-sm text-amber-900 leading-relaxed">
            {explanation?.content.what_this_does_not_mean ?? "…"}
          </p>
        </div>
      </Card>

      {explanation && explanation.content.possible_reasons.length > 0 && (
        <Card className="mb-4">
          <h2 className="font-bold text-base mb-2">{t("notice.reasons")}</h2>
          <ul className="space-y-1.5">
            {explanation.content.possible_reasons.map((r, i) => (
              <li key={i} className="text-sm text-stone-700 flex gap-2">
                <span className="text-saffron font-bold" aria-hidden>•</span>
                {r}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card className="mb-4">
        <button
          onClick={() => setShowOfficial(!showOfficial)}
          className="text-sm font-semibold text-india-green underline"
          aria-expanded={showOfficial}
        >
          {showOfficial ? t("notice.officialHide") : t("notice.officialShow")}
        </button>
        {showOfficial && (
          <div className="mt-3 text-xs text-stone-600 bg-stone-50 border border-stone-200  p-3 whitespace-pre-line max-h-72 overflow-y-auto">
            {notice.official_text}
          </div>
        )}
      </Card>

      {explanation && (
        <Card className="mb-4">
          <CitationChips citations={explanation.citations} />
          <p className="mt-3 text-[11px] text-stone-500 leading-relaxed">
            {explanation.scope_statement[locale] ?? explanation.scope_statement.en}
          </p>
        </Card>
      )}

      <Link
        to={`/notices/${id}/journey`}
        className="app-primary"
      >
        {t("notice.continue")} →
      </Link>
    </div>
  );
}
