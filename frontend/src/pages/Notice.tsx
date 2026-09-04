import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
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
  if (notice.section.replace(/\s/g, "").startsWith("142(1)")) return <Navigate to={`/notices/${id}/scrutiny`} replace />;

  return (
    <div className="app-page">
      <p className="app-eyebrow">[ TM / NOTICE / 01 ]</p>
      <h1 className="app-title">{notice.title[locale] ?? notice.title.en}</h1>
      <p className="app-lead">{notice.section} · AY {notice.assessment_year}</p>
      <Stepper current={0} />

      <div className="app-content-spacing">
        <div className="mb-2">
          <SavedGuidanceBadge show={explanation?.demo_mode || explanation?.source === "static"} />
        </div>

        <Card className="mb-4">
          <p className="app-section-label">[ {t("notice.plain")} ]</p>
          <p className="app-body">
            {explanation?.content.plain_language ?? "…"}
          </p>
          <details className="notice-boundary">
            <summary>{t("notice.notMean")}</summary>
            <p className="app-body mt-3">{explanation?.content.what_this_does_not_mean ?? "…"}</p>
          </details>
        </Card>

        <Link
          to={`/notices/${id}/journey`}
          className="app-primary mb-4"
        >
          {t("notice.continue")} →
        </Link>

        {explanation && explanation.content.possible_reasons.length > 0 && (
          <Card className="mb-4">
            <details>
            <summary className="app-section-label">[ {t("notice.reasons")} ]</summary>
            <ol className="reason-list">
              {explanation.content.possible_reasons.map((r, i) => <li key={i}><span>{String(i + 1).padStart(2, "0")}</span>{r}</li>)}
            </ol>
            </details>
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
      </div>
    </div>
  );
}
