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
    ]).then(([owned, scrutiny]) => setNotices(scrutiny && !owned.some(n => n.id === scrutiny.id) ? [...owned, scrutiny] : owned)).catch(() => setNotices([]));
  }, [citizenId, navigate]);

  if (!notices) return <div className="app-page"><div className="app-loading">LOADING NOTICES</div></div>;

  return (
    <div className="app-page">
      <p className="app-eyebrow">[ TM / NOTICE INDEX ]</p>
      <h1 className="app-title">{t("dash.title")}</h1>
      <p className="app-lead">Select a fictional notice to understand what it means and prepare the next step.</p>
      {notices.length === 0 ? <div className="app-empty mt-8"><p className="app-section-label">[ NO NOTICES FOUND ]</p><p>There are no demo notices available for this profile.</p></div> : <div className="app-grid">
        {notices.map((n) => (
          <Card key={n.id}>
            <p className="app-section-label">[ NOTICE / {n.id.toUpperCase()} ]</p>
            <h2 className="text-2xl font-medium leading-tight">{n.title[locale] ?? n.title.en}</h2>
            <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
              <div><p className="app-eyebrow">{t("dash.amount")}</p><p className="font-semibold mt-1">{formatINR(n.amount_in_question)}</p></div>
              <div><p className="app-eyebrow">{t("dash.respondBy")}</p><p className="font-semibold mt-1">{n.due_date ?? "—"}</p></div>
            </div>
            <div className="mt-5"><StatusChip status={n.status} daysRemaining={n.days_remaining} /></div>
            <div className="mt-6">{n.supported ? <Link to={`/notices/${n.id}`} className="app-primary">{t("dash.start")} →</Link> : <Link to={`/notices/${n.id}/unsupported`} className="app-primary">{t("dash.unsupported")} →</Link>}</div>
          </Card>
        ))}
      </div>}
    </div>
  );
}
