import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, formatINR, NoticeCard as NoticeCardT, store } from "../lib";
import { Card, StatusChip } from "../components";

export default function Dashboard() {
  const { t, locale } = useI18n();
  const navigate = useNavigate();
  const [notices, setNotices] = useState<NoticeCardT[] | null>(null);
  const citizenId = store.citizenId();

  useEffect(() => {
    if (!citizenId) {
      navigate("/login");
      return;
    }
    Promise.all([
      api.notices(citizenId),
      api.notice("N-2026-003").catch(() => null),
    ])
      .then(([owned, scrutiny]) =>
        setNotices(
          scrutiny && !owned.some((n) => n.id === scrutiny.id)
            ? [...owned, scrutiny]
            : owned
        )
      )
      .catch(() => setNotices([]));
  }, [citizenId, navigate]);

  if (!notices)
    return (
      <div className="app-page">
        <div className="app-loading">LOADING NOTICES...</div>
      </div>
    );

  return (
    <div className="app-page">
      <p className="app-eyebrow font-semibold tracking-wider text-slate-500">
        {locale === "hi" ? "नोटिस सूची" : "ACTIVE NOTICES"}
      </p>
      <h1 className="app-title">{t("dash.title")}</h1>
      <p className="app-lead">{t("dash.subtitle")}</p>

      {notices.length === 0 ? (
        <div className="app-empty mt-8">
          <p className="app-section-label font-bold text-slate-600">
            {locale === "hi" ? "कोई नोटिस नहीं मिला" : "NO NOTICES FOUND"}
          </p>
          <p>{t("dash.noNotices")}</p>
        </div>
      ) : (
        <div className="app-grid">
          {notices.map((n) => (
            <Card key={n.id}>
              <p className="app-section-label font-bold text-blue-600">
                NOTICE · {n.id.toUpperCase()}
              </p>
              <h2 className="text-2xl font-bold leading-tight text-slate-900 mt-1">
                {n.title[locale] ?? n.title.en}
              </h2>
              <p className="notice-record-meta font-semibold text-slate-700 mt-1">
                {n.section} · AY {n.assessment_year}
                {n.official_reference ? ` · ${n.official_reference}` : ""}
              </p>
              <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="app-eyebrow text-slate-500">{t("dash.amount")}</p>
                  <p className="font-bold text-slate-900 mt-1">{formatINR(n.amount_in_question)}</p>
                </div>
                <div>
                  <p className="app-eyebrow text-slate-500">{t("dash.respondBy")}</p>
                  <p className="font-bold text-slate-900 mt-1">{n.due_date ?? "—"}</p>
                </div>
              </div>
              <div className="mt-5">
                <StatusChip status={n.status} daysRemaining={n.days_remaining} />
              </div>
              <div className="mt-6">
                {n.supported ? (
                  <Link to={`/notices/${n.id}`} className="app-primary">
                    {t("dash.start")} →
                  </Link>
                ) : (
                  <Link to={`/notices/${n.id}/unsupported`} className="app-primary">
                    {t("dash.unsupported")} →
                  </Link>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
