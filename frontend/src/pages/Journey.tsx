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
  const [questions, setQuestions] = useState<Question[] | null>(null);
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
    if (!id || !questions || questions.length === 0) return;
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
  if (!questions) return <div className="app-page"><div className="app-loading">PREPARING GUIDED QUESTIONS</div></div>;
  const q = questions[qIndex];
  const positionLabel = (pos?: string) =>
    pos === "agree" ? "AGREE" : pos === "disagree" ? "DISAGREE" : "NOT SURE";

  return (
    <div className="app-page">
      <Stepper current={stepperFor(phase)} />

      {phase === "questions" && (
        <div>
          <h1 className="app-title">{t("j.qTitle")}</h1>
          <p className="text-sm text-stone-600 mt-1 mb-5">{t("j.qHelp")}</p>
          {q && (
            <Card>
              <div className="question-progress"><span>QUESTION {String(qIndex + 1).padStart(2, "0")}</span><span>{qIndex + 1} / {questions.length}</span></div>
              <div className="question-meter" aria-hidden="true"><i style={{ width: `${((qIndex + 1) / questions.length) * 100}%` }} /></div>
              <h2 className="question-title">{q.text}</h2>
              {q.help && <p className="text-sm text-stone-500 mt-2">{q.help}</p>}
              <div className="mt-5 grid gap-2">
                {q.options.map((o) => (
                  <button
                    key={o.id}
                    onClick={() => answer(o.id)}
                    className="text-left border border-stone-200 hover:border-blue-600 hover:text-blue-600 px-4 py-3 font-semibold transition-colors"
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </Card>
          )}
          {qIndex > 0 ? (
            <button onClick={() => setQIndex(qIndex - 1)} className="app-back">
              ← {t("j.back")}
            </button>
          ) : (
            <Link to={`/notices/${id}`} className="app-back">← {t("j.back")}</Link>
          )}
        </div>
      )}

      {phase === "checklist" && result?.checklist && (
        <div>
          <h1 className="app-title">{t("j.checklistTitle")}</h1>
          <p className="text-sm text-stone-600 mt-1 mb-4">{t("j.checklistSub")}</p>
          <Card className="mb-4 workflow-guidance app-dots">
            <p className="app-section-label">[ YOUR GUIDED PATH ]</p>
            <h2>{result.path?.headline[locale] ?? result.path?.headline.en}</h2>
            <p className="app-body">{result.path?.guidance[locale] ?? result.path?.guidance.en}</p>
          </Card>
          <div className="checklist-list">
            {result.checklist.map((item, index) => (
              <Card key={item.id}>
                <p className="checklist-title"><span>{String(index + 1).padStart(2, "0")}</span>{item.title[locale] ?? item.title.en}</p>
                <details><summary>{t("j.why")} ↓</summary><p className="app-body">{item.why_needed[locale] ?? item.why_needed.en}</p></details>
              </Card>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <PrimaryButton onClick={() => setPhase("draft")}>{t("j.next")} →</PrimaryButton>
            <button className="app-back !mt-0" onClick={() => setPhase("questions")}>← {t("j.back")}</button>
          </div>
        </div>
      )}

      {phase === "draft" && (
        <div>
          <h1 className="app-title">{t("j.draftTitle")}</h1>
          <p className="text-sm text-stone-600 mt-1 mb-4">{t("j.draftSub")}</p>
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={() => store.setDraft(id, draft)}
            placeholder={t("j.draftPlaceholder")}
            rows={14}
            className="w-full border border-stone-300 focus:border-blue-600 p-4 text-sm leading-relaxed font-mono outline-none"
          />
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <PrimaryButton
              onClick={() => {
                store.setDraft(id, draft);
                setPhase("review");
              }}
            >
              {t("j.acceptDraft")} →
            </PrimaryButton>
            <button className="app-back !mt-0" onClick={() => setPhase("checklist")}>← {t("j.back")}</button>
          </div>
        </div>
      )}

      {phase === "review" && result?.path && (
        <div>
          <h1 className="app-title">{t("j.reviewTitle")}</h1>
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
          <div className="flex flex-wrap items-center gap-3">
            <PrimaryButton onClick={() => setPhase("final")}>{t("j.next")} →</PrimaryButton>
            <button className="app-back !mt-0" onClick={() => setPhase("draft")}>← {t("j.back")}</button>
          </div>
        </div>
      )}

      {phase === "final" && result?.official_step && (
        <div>
          <p className="app-eyebrow">[ TM / OFFICIAL HANDOFF / 04 ]</p>
          <h1 className="app-title">{t("j.finalTitle")}</h1>
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
          <div className="notice-boundary mb-4"><p className="app-section-label">[ IMPORTANT BOUNDARY ]</p><p className="app-body">{result.official_step.boundary[locale] ?? result.official_step.boundary.en}</p></div>
          <div className="grid gap-2">
            <a
              href={result.official_step.url}
              target="_blank"
              rel="noopener noreferrer"
              className="app-primary text-center"
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
          <div className="mt-6 flex flex-wrap items-center justify-center gap-5">
            <button className="app-back !mt-0" onClick={() => setPhase("review")}>← {t("j.back")}</button>
            <Link to="/notices" className="text-sm text-stone-500 underline">
              {t("j.restart")}
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
