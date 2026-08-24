import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, formatINR, NoticeCard as NoticeCardT, store } from "../lib";
import { Card, StatusChip } from "../components";

export default function Dashboard() {
  const { t, locale } = useI18n();
  const navigate = useNavigate();
  const [notices, setNotices] = useState<NoticeCardT[]>([]);
  const citizenId = store.citizenId();

  useEffect(() => {
    if (!citizenId) {
      navigate("/login");
      return;
    }
    api.notices(citizenId).then(setNotices).catch(() => setNotices([]));
  }, [citizenId, navigate]);

  return (
    <div className="px-4 max-w-md mx-auto py-6">
      <h1 className="text-xl font-extrabold mb-4">{t("dash.title")}</h1>
      {notices.map((n) => (
        <Card key={n.id} className="mb-4">
          <h2 className="font-bold text-ink leading-snug">{n.title[locale] ?? n.title.en}</h2>
          <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-xs text-stone-500">{t("dash.amount")}</p>
              <p className="font-bold">{formatINR(n.amount_in_question)}</p>
            </div>
            <div>
              <p className="text-xs text-stone-500">{t("dash.respondBy")}</p>
              <p className="font-bold">{n.due_date ?? "—"}</p>
            </div>
          </div>
          <div className="mt-3">
            <StatusChip status={n.status} daysRemaining={n.days_remaining} />
          </div>
          <div className="mt-4">
            {n.supported ? (
              <Link
                to={`/notices/${n.id}`}
                className="inline-flex bg-saffron text-white font-semibold rounded-xl px-4 py-2.5"
              >
                {t("dash.start")} →
              </Link>
            ) : (
              <Link
                to={`/notices/${n.id}/unsupported`}
                className="inline-flex bg-stone-800 text-white font-semibold rounded-xl px-4 py-2.5"
              >
                {t("dash.unsupported")}
              </Link>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}
