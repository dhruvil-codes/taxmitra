import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, Question, ResolveResult, formatINR, store } from "../lib";
import { Card, PrimaryButton, Stepper } from "../components";

type Phase = "questions" | "checklist" | "draft" | "review" | "final";

export default function Journey() {
  const { id } = useParams<{ id: string }>();
  const { t, locale } = useI18n();
  const [phase, setPhase] = useState<Phase>("questions");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [qIndex, setQIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>(() => (id ? store.answers(id) : {}));
  const [result, setResult] = useState<ResolveResult | null>(null);
  const [draft, setDraft] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.questions(id, locale).then((r) => setQuestions(r.questions)).catch(() => setQuestions([]));
  }, [id, locale]);

  const answer = (optionId: string) => {
    if (!id || questions.length === 0) return;
    const q = questions[qIndex];
    const next = { ...answers, [q.id]: optionId };
    setAnswers(next);
    store.setAnswers(id, next);
    if (qIndex + 1 < questions.length) {
      setQIndex(qIndex + 1);
    } else {
      api.resolve(id, next).then((r) => {
        setResult(r);
        setDraft(r.draft ?? "");
        setPhase("checklist");
      });
    }
  };

  const stepperFor = (p: Phase): 0 | 1 | 2 | 3 =>
    p === "questions" ? 1 : p === "checklist" ? 2 : p === "draft" ? 2 : 3;

  if (!id) return null;
  const q = questions[qIndex];
  const positionLabel = (pos?: string) =>
    pos === "agree" ? "✓ Agree" : pos === "disagree" ? "✕ Disagree" : "? Not sure";

  return (
    <div className="px-4 max-w-xl mx-auto py-6">
      <Stepper current={stepperFor(phase)} />

      {phase === "questions" && (
        <div>
          <h1 className="text-xl font-extrabold">{t("j.qTitle")}</h1>
          <p className="text-sm text-stone-600 mt-1 mb-5">{t("j.qHelp")}</p>
          {q && (
            <Card>
              <p className="text-xs text-stone-400 mb-1">
                {qIndex + 1} / {questions.length}
              </p>
              <h2 className="text-lg font-bold leading-snug">{q.text}</h2>
              {q.help && <p className="text-sm text-stone-500 mt-2">{q.help}</p>}
              <div className="mt-5 grid gap-2">
                {q.options.map((o) => (
                  <button
                    key={o.id}
                    onClick={() => answer(o.id)}
                    className="text-left border-2 border-stone-200 hover:border-saffron hover:bg-saffron-soft rounded-xl px-4 py-3 font-semibold transition"
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </Card>
          )}
          {qIndex > 0 && (
            <button
              onClick={() => setQIndex(qIndex - 1)}
              className="mt-4 text-sm text-stone-500 underline"
            >
              ← {t("j.back")}
            </button>
          )}
        </div>
      )}

      {phase === "checklist" && result?.checklist && (
        <div>
          <h1 className="text-xl font-extrabold">{t("j.checklistTitle")}</h1>
          <p className="text-sm text-stone-600 mt-1 mb-4">{t("j.checklistSub")}</p>
          <Card className="mb-4 bg-india-green-soft border-green-200">
            <p className="font-bold text-india-green leading-snug">
              {result.path?.headline[locale] ?? result.path?.headline.en}
            </p>
            <p className="text-sm text-stone-700 mt-1.5 leading-relaxed">
              {result.path?.guidance[locale] ?? result.path?.guidance.en}
            </p>
          </Card>
          {result.checklist.map((item) => (
            <Card key={item.id} className="mb-3">
              <p className="font-semibold flex items-start gap-2">
                <span className="text-india-green font-bold" aria-hidden>✓</span>
                {item.title[locale] ?? item.title.en}
              </p>
              <details className="mt-1.5">
                <summary className="text-sm text-saffron font-medium cursor-pointer">
                  {t("j.why")}
                </summary>
                <p className="text-sm text-stone-600 mt-1.5 leading-relaxed">
                  {item.why_needed[locale] ?? item.why_needed.en}
                </p>
              </details>
            </Card>
          ))}
          <PrimaryButton onClick={() => setPhase("draft")}>{t("j.next")} →</PrimaryButton>
        </div>
      )}

      {phase === "draft" && (
        <div>
          <h1 className="text-xl font-extrabold">{t("j.draftTitle")}</h1>
          <p className="text-sm text-stone-600 mt-1 mb-4">{t("j.draftSub")}</p>
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={() => store.setDraft(id, draft)}
            placeholder={t("j.draftPlaceholder")}
            rows={14}
            className="w-full border-2 border-stone-200 focus:border-saffron rounded-xl p-4 text-sm leading-relaxed font-mono"
          />
          <div className="mt-4">
            <PrimaryButton
              onClick={() => {
                store.setDraft(id, draft);
                setPhase("review");
              }}
            >
              {t("j.acceptDraft")} →
            </PrimaryButton>
          </div>
        </div>
      )}

      {phase === "review" && result?.path && (
        <div>
          <h1 className="text-xl font-extrabold">{t("j.reviewTitle")}</h1>
          <Card className="my-4">
            <dl className="text-sm divide-y divide-stone-100">
              <div className="py-2 flex justify-between gap-4">
                <dt className="text-stone-500">{t("j.reviewIssue")}</dt>
                <dd className="font-semibold text-right">143(1)(a) income mismatch</dd>
              </div>
              <div className="py-2 flex justify-between gap-4">
                <dt className="text-stone-500">{t("j.reviewAmount")}</dt>
                <dd className="font-semibold">{formatINR(45000)}</dd>
              </div>
              <div className="py-2 flex justify-between gap-4">
                <dt className="text-stone-500">{t("j.reviewPosition")}</dt>
                <dd className="font-semibold">{positionLabel(result.path.position)}</dd>
              </div>
              <div className="py-2 flex justify-between gap-4">
                <dt className="text-stone-500">{t("j.reviewDocs")}</dt>
                <dd className="font-semibold">{result.checklist?.length ?? 0}</dd>
              </div>
              <div className="py-2 flex justify-between gap-4">
                <dt className="text-stone-500">{t("j.reviewDeadline")}</dt>
                <dd className="font-semibold">{result.deadline?.due_date ?? "—"}</dd>
              </div>
            </dl>
          </Card>
          <p className="text-sm text-stone-600 mb-4">{t("j.reviewNote")}</p>
          <PrimaryButton onClick={() => setPhase("final")}>{t("j.next")} →</PrimaryButton>
        </div>
      )}

      {phase === "final" && result?.official_step && (
        <div>
          <h1 className="text-xl font-extrabold text-saffron">{t("j.finalTitle")}</h1>
          <Card className="my-4 space-y-4">
            <div>
              <p className="text-xs font-bold uppercase text-stone-500">{t("j.finalWhat")}</p>
              <p className="font-semibold">
                {result.official_step.label[locale] ?? result.official_step.label.en}
              </p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-stone-500">{t("j.finalWhen")}</p>
              <p className="font-semibold">
                {result.deadline?.due_date}{" "}
                {result.deadline?.days_remaining != null && result.deadline.days_remaining >= 0
                  ? `(${t("dash.daysLeft", { n: String(result.deadline.days_remaining) })})`
                  : ""}
              </p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-stone-500">{t("j.finalNeed")}</p>
              <ul className="text-sm mt-1 space-y-1">
                {result.checklist?.map((c) => (
                  <li key={c.id} className="text-stone-700">• {c.title[locale] ?? c.title.en}</li>
                ))}
              </ul>
            </div>
          </Card>
          <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-4 text-sm text-amber-900 font-semibold leading-relaxed mb-4">
            ⚠️ {result.official_step.boundary[locale] ?? result.official_step.boundary.en}
          </div>
          <div className="grid gap-2">
            <a
              href={result.official_step.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-center bg-india-green text-white font-bold rounded-xl px-5 py-3.5"
            >
              {t("j.continuePortal")}
            </a>
            <button
              onClick={() => {
                navigator.clipboard?.writeText(draft);
                setCopied(true);
              }}
              className="text-sm text-stone-600 underline py-2"
            >
              {copied ? t("j.finalCopied") : t("j.finalCopy")}
            </button>
          </div>
          <Link to="/notices" className="block text-center text-sm text-stone-400 underline mt-6">
            {t("j.restart")}
          </Link>
        </div>
      )}
    </div>
  );
}
