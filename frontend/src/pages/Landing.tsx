import { useNavigate } from "react-router-dom";
import { useI18n } from "../i18n";
import { Card, PrimaryButton } from "../components";

export default function Landing() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const four = [
    ["landing.q1", "landing.q1.sub"],
    ["landing.q2", "landing.q2.sub"],
    ["landing.q3", "landing.q3.sub"],
    ["landing.q4", "landing.q4.sub"],
  ];
  const gptRows = ["landing.gpt.1", "landing.gpt.2", "landing.gpt.3"];
  return (
    <div>
      <section className="px-4 pt-10 pb-8 text-center max-w-2xl mx-auto">
        <p className="text-5xl mb-3" aria-hidden>😰 → 😌</p>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-ink leading-tight">
          {t("landing.hero")}
        </h1>
        <p className="mt-3 text-stone-600 leading-relaxed">{t("landing.sub")}</p>
        <div className="mt-6">
          <PrimaryButton onClick={() => navigate("/guide")}>{t("landing.cta")} →</PrimaryButton>
        </div>
      </section>

      <section className="px-4 max-w-2xl mx-auto" aria-label={t("landing.four.title")}>
        <h2 className="text-center font-bold text-lg mb-4">{t("landing.four.title")}</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {four.map(([q, s]) => (
            <Card key={q} className="flex gap-3 items-start">
              <div className="w-8 h-8 shrink-0 rounded-full bg-saffron-soft text-saffron font-bold flex items-center justify-center">
                {q === "landing.q1" ? "1" : q === "landing.q2" ? "2" : q === "landing.q3" ? "3" : "4"}
              </div>
              <div>
                <h3 className="font-bold text-ink">{t(q)}</h3>
                <p className="text-sm text-stone-600 mt-0.5">{t(s)}</p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className="px-4 max-w-2xl mx-auto mt-10">
        <Card>
          <h2 className="font-bold text-lg mb-3">{t("landing.gpt.title")}</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase text-stone-500">
                  <th className="py-2 pr-2">{t("landing.gpt.col1")}</th>
                  <th className="py-2 pr-2">{t("landing.gpt.col2")}</th>
                  <th className="py-2 text-saffron">{t("landing.gpt.col3")}</th>
                </tr>
              </thead>
              <tbody>
                {gptRows.map((r) => (
                  <tr key={r} className="border-t border-stone-100">
                    <td className="py-2 pr-2 text-stone-600">{t(r)}</td>
                    <td className="py-2 pr-2 text-stone-400">{t(r + "b")}</td>
                    <td className="py-2 font-medium text-ink">{t(r + "c")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-stone-500 italic">
            We use AI to remove the need to know what questions to ask.
          </p>
        </Card>
      </section>

      <section className="px-4 max-w-2xl mx-auto my-10">
        <p className="text-xs text-stone-500 text-center leading-relaxed">{t("landing.trust")}</p>
      </section>
    </div>
  );
}
