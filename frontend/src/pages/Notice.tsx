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

  if (error) return <div className="app-page"><div className="app-empty"><p className="app-section-label">[ NOTICE UNAVAILABLE ]</p><p>We could not load this notice. Return to your notices and try again.</p></div><Link className="app-back" to="/notices">← Back to notices</Link></div>;
  if (!notice) return <div className="app-page"><div className="app-loading">LOADING NOTICE</div></div>;

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
        <div className="notice-boundary">
          <p className="app-section-label">[ {t("notice.notMean")} ]</p>
          <p className="app-body">{explanation?.content.what_this_does_not_mean ?? "…"}</p>
        </div>
      </Card>

      {explanation && explanation.content.possible_reasons.length > 0 && (
        <Card className="mb-4">
          <h2 className="app-section-label">[ {t("notice.reasons")} ]</h2>
          <ol className="reason-list">
            {explanation.content.possible_reasons.map((r, i) => <li key={i}><span>{String(i + 1).padStart(2, "0")}</span>{r}</li>)}
          </ol>
        </Card>
      )}

      <Card className="mb-4">
        <button
          onClick={() => setShowOfficial(!showOfficial)}
          className="app-text-action"
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
