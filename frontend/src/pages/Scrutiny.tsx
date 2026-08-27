import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, ApiError, NoticeCard, OFFICIAL_EFILING_PORTAL_URL, ScrutinyQuestion, ScrutinyRequestsResult, ScrutinyResolveResult, store, verifiedIncomeTaxUrl } from "../lib";
import { Card, PrimaryButton, Stepper } from "../components";

type Stage = "requests" | "confirm" | "questions" | "result" | "draft" | "review" | "final" | "refusal";
const text = (value: Record<string, string> | undefined, locale: string) => value?.[locale] ?? value?.en ?? "";

function ErrorState({ error, retry }: { error: ApiError | Error; retry: () => void }) {
  const message = error instanceof ApiError && error.status === 404 ? "This notice could not be found." : error instanceof ApiError && error.status === 429 ? "Too many requests. Please wait, then try again." : error instanceof ApiError && error.status === 503 ? "Guidance is temporarily unavailable." : "We could not load the guidance service.";
  return <div className="app-empty"><p className="app-section-label">[ GUIDANCE UNAVAILABLE ]</p><p>{message}</p><button className="app-primary mt-5" onClick={retry}>TRY AGAIN</button></div>;
}

export default function Scrutiny() {
  const { id = "" } = useParams();
  const { locale, t } = useI18n();
  const restored = store.scrutinyStage(id) as Stage;
  const isUploaded = store.uploadedNoticeId() === id;
  const [stage, setStageState] = useState<Stage>(restored === "questions" && !store.extractionConfirmed(id) ? "requests" : restored);
  const [notice, setNotice] = useState<NoticeCard | null>(null);
  const [data, setData] = useState<ScrutinyRequestsResult | null>(null);
  const [questions, setQuestions] = useState<ScrutinyQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>(() => store.answers(id));
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<ScrutinyResolveResult | null>(null);
  const [draft, setDraft] = useState(() => store.draft(id) ?? "");
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const setStage = (next: Stage) => { setStageState(next); store.setScrutinyStage(id, next); window.scrollTo({ top: 0, behavior: "smooth" }); };

  const load = () => {
    const controller = new AbortController(); setLoading(true); setError(null);
    Promise.all([
      isUploaded ? Promise.resolve(null) : api.notice(id),
      api.scrutinyRequests(id, locale, true, controller.signal),
    ])
      .then(([n, r]) => { setNotice(n); setData(r); setLoading(false); })
      .catch((e) => { if (e.name !== "AbortError") { setError(e); setLoading(false); } });
    return () => controller.abort();
  };
  useEffect(load, [id, locale]);

  const confirm = async () => {
    setLoading(true); setError(null);
    try { const response = await api.scrutinyQuestions(id, locale, true); store.setExtractionConfirmed(id, true); setQuestions(response.questions); setIndex(Math.max(0, response.questions.findIndex(q => !answers[q.id]))); setStage("questions"); }
    catch (e) { setError(e as Error); }
    finally { setLoading(false); }
  };
  const reject = async () => {
    setLoading(true);
    try { setResult(await api.resolveScrutiny(id, {}, false)); setStage("refusal"); }
    catch (e) { setError(e as Error); }
    finally { setLoading(false); }
  };
  const answer = async (value: string) => {
    const q = questions[index]; const next = { ...answers, [q.id]: value }; setAnswers(next); store.setAnswers(id, next);
    if (index < questions.length - 1) { setIndex(index + 1); return; }
    setLoading(true); setError(null);
    try { const resolved = await api.resolveScrutiny(id, next, true); setResult(resolved); setDraft(store.draft(id) ?? resolved.draft ?? ""); setStage("result"); }
    catch (e) { setError(e as Error); }
    finally { setLoading(false); }
  };
  const ensureQuestions = async () => { if (!questions.length) { const r = await api.scrutinyQuestions(id, locale, true); setQuestions(r.questions); } setStage("questions"); };

  if (loading && !data) return <div className="app-page"><div className="app-loading">READING REQUESTED ITEMS</div></div>;
  if (error && !data) return <div className="app-page"><ErrorState error={error} retry={load} />{isUploaded ? <Link to="/upload" className="app-primary mt-5">START A NEW PDF SESSION →</Link> : <Link to="/notices" className="app-back">← BACK TO NOTICES</Link>}</div>;
  if (!data || (!notice && !isUploaded)) return null;
  const requests = data.requests ?? [];
  const q = questions[index];
  const step = stage === "requests" || stage === "confirm" ? 0 : stage === "questions" ? 1 : stage === "result" || stage === "draft" ? 2 : 3;

  return <div className="app-page scrutiny-page">
    <Stepper current={step} />
    {error && <div className="mb-5"><ErrorState error={error} retry={() => setError(null)} /></div>}

    {stage === "requests" && <>
      <p className="app-eyebrow">[ TM / SCRUTINY / REQUESTS ]</p><h1 className="app-title">{locale === "hi" ? "अधिकारी ने क्या मांगा है" : "What the officer has asked for"}</h1>
      <div className="scrutiny-meta"><span>{notice?.section ?? "142(1)"}</span>{notice?.assessment_year && <span>AY {notice.assessment_year}</span>}{notice?.official_reference && <span>{notice.official_reference}</span>}{notice?.due_date && <span>{notice.due_date}</span>}</div>
      <p className="app-lead">{locale === "hi" ? `${requests.length} अनुरोध नोटिस के अनुलग्नक से निकाले गए हैं। पुष्टि से पहले हर अनुरोध जांचें।` : `${requests.length} requests were extracted from the notice annexure. Review every item before confirming.`}</p>
      <div className="scrutiny-list">{requests.map((r, i) => <Card key={r.id}>
        <p className="app-section-label">[ REQUEST {String(i + 1).padStart(2, "0")} / {r.response_section.toUpperCase()} ]</p>
        <blockquote>{r.original_text}</blockquote>
        <div className="scrutiny-explain"><div><b>{locale === "hi" ? "आसान भाषा में" : "In plain language"}</b><p>{text(r.plain_language_explanation, locale)}</p></div><div><b>{locale === "hi" ? "यह क्यों मांगा गया" : "Why it is required"}</b><p>{text(r.why_required, locale)}</p></div></div>
        <details><summary>{locale === "hi" ? "अपेक्षित प्रमाण देखें" : "See expected evidence"}</summary><ul>{r.required_evidence.map((e, j) => <li key={j}>{text(e, locale)}</li>)}</ul></details>
        {r.citations.map(c => <a key={c.id} className="scrutiny-source" href={c.official_url} target="_blank" rel="noreferrer">{c.source_name} · {c.section} ↗</a>)}
      </Card>)}</div>
      <div className="notice-boundary"><p className="app-section-label">[ {isUploaded ? "CONFIRMED EXTRACTION" : "HUMAN CONFIRMATION REQUIRED"} ]</p><p className="app-body">{isUploaded ? (locale === "hi" ? "आपने PDF निष्कर्षण की पुष्टि की है। अब backend इन्हीं अनुरोधों से सवाल तैयार करेगा।" : "You confirmed this PDF extraction. The backend will now build questions from these exact requests.") : (locale === "hi" ? "यह काल्पनिक PDF निष्कर्ष है। Tax Mitra तब तक आगे नहीं बढ़ेगा जब तक आप अनुरोधों की पुष्टि नहीं करते।" : "This is a synthetic PDF extraction. Tax Mitra will not guide a response until you confirm the requested items.")}</p></div>
      <div className="flex flex-wrap items-center gap-3"><PrimaryButton onClick={isUploaded ? ensureQuestions : () => setStage("confirm")}>{isUploaded ? (locale === "hi" ? "रिकॉर्ड जांचें" : "CHECK YOUR RECORDS") : (locale === "hi" ? "सूची की पुष्टि करें" : "CONFIRM REQUEST LIST")} →</PrimaryButton><Link className="app-back !mt-0" to={isUploaded ? "/upload" : `/notices/${id}`}>← {t("j.back")}</Link></div>
    </>}

    {stage === "confirm" && <Card className="confirmation-card app-dots"><p className="app-section-label">[ CHECKPOINT ]</p><h1>{locale === "hi" ? "क्या निकाली गई सूची नोटिस से मेल खाती है?" : "Does the extracted list match the notice?"}</h1><p className="app-body">{locale === "hi" ? `सभी ${requests.length} अनुरोधों की तुलना मूल शब्दों से करें। अनुमान न लगाएं।` : `Compare all ${requests.length} requests with the original wording. Do not confirm if anything is missing or incorrect.`}</p><div className="confirmation-actions"><PrimaryButton onClick={confirm}>{locale === "hi" ? "हाँ, सही है" : "YES, IT LOOKS CORRECT"} →</PrimaryButton><button onClick={reject}>{locale === "hi" ? "कुछ गलत है" : "SOMETHING LOOKS WRONG"}</button></div><button className="app-back" onClick={() => setStage("requests")}>← {t("j.back")}</button></Card>}

    {stage === "questions" && q && <><p className="app-eyebrow">[ EVIDENCE CHECK / {String(index + 1).padStart(2, "0")} ]</p><h1 className="app-title">{locale === "hi" ? "अपने रिकॉर्ड जांचें" : "Check your records"}</h1><Card><div className="question-progress"><span>QUESTION {index + 1}</span><span>{index + 1} / {questions.length}</span></div><div className="question-meter"><i style={{width:`${((index + 1) / questions.length) * 100}%`}} /></div><h2 className="question-title">{q.text}</h2><p className="app-body mt-3">{q.help}</p><div className="answer-grid">{q.options.map(o => <button className={answers[q.id] === o.id ? "is-selected" : ""} key={o.id} onClick={() => answer(o.id)}>{o.label}<span>→</span></button>)}</div></Card><button className="app-back" onClick={() => index > 0 ? setIndex(index - 1) : setStage("requests")}>← {t("j.back")}</button></>}

    {stage === "result" && result?.path && <><p className="app-eyebrow">[ DETERMINISTIC RESULT / {result.path.path_id.toUpperCase()} ]</p><h1 className="app-title">{text(result.path.headline, locale)}</h1>{result.path.professional_help_recommended && <div className="notice-boundary"><p className="app-section-label">[ PROFESSIONAL REVIEW RECOMMENDED ]</p><p className="app-body">{locale === "hi" ? "अंतिम रुख लेने से पहले रिकॉर्ड की विशेषज्ञ समीक्षा कराएं।" : "Have a tax professional review the uncertain records before taking a final position."}</p></div>}<div className="checklist-list">{result.checklist?.map(item => <Card key={item.id}><p className="checklist-title"><span>{item.status.toUpperCase()}</span>{text(item.title, locale)}</p><ul className="evidence-list">{item.required_evidence.map((e,i)=><li key={i}>{text(e,locale)}</li>)}</ul></Card>)}</div><div className="flex flex-wrap gap-3"><PrimaryButton onClick={() => setStage("draft")}>{locale === "hi" ? "मसौदा देखें" : "REVIEW RESPONSE DRAFT"} →</PrimaryButton><button className="app-back !mt-0" onClick={ensureQuestions}>← {locale === "hi" ? "जवाब बदलें" : "CHANGE ANSWERS"}</button></div></>}

    {stage === "draft" && <><p className="app-eyebrow">[ RESPONSE PACKAGE / DRAFT ]</p><h1 className="app-title">{t("j.draftTitle")}</h1><p className="app-lead mb-5">{t("j.draftSub")}</p><textarea className="scrutiny-draft" rows={20} value={draft} onChange={e=>setDraft(e.target.value)} onBlur={()=>store.setDraft(id,draft)} /><div className="flex flex-wrap items-center gap-3"><PrimaryButton onClick={()=>{store.setDraft(id,draft);setStage("review")}}>{t("j.acceptDraft")} →</PrimaryButton><button className="app-back !mt-0" onClick={()=>setStage("result")}>← {t("j.back")}</button></div></>}

    {stage === "review" && result && <><p className="app-eyebrow">[ FINAL REVIEW / HUMAN APPROVAL ]</p><h1 className="app-title">{t("j.reviewTitle")}</h1><div className="review-grid"><Card><p className="app-section-label">[ COVERAGE ]</p>{result.checklist?.map(x=><p key={x.id} className="review-row"><span>{text(x.title,locale)}</span><b>{x.status.toUpperCase()}</b></p>)}</Card><Card className="deadline-card"><p className="app-section-label">[ RESPONSE DEADLINE ]</p><strong>{result.deadline?.due_date ?? "—"}</strong><p>{locale === "hi" ? "आधिकारिक नोटिस में दिखाई गई तारीख" : "Date shown on the official notice"}</p></Card></div><div className="notice-boundary"><p className="app-section-label">[ REVIEW BEFORE CONTINUING ]</p><p className="app-body">{locale === "hi" ? "मसौदे और प्रमाण को वास्तविक रिकॉर्ड से मिलाएं। कुछ भी अभी जमा नहीं हुआ है।" : "Match the draft and evidence against the taxpayer's actual records. Nothing has been submitted."}</p></div><div className="flex flex-wrap items-center gap-3"><PrimaryButton onClick={()=>setStage("final")}>{locale === "hi" ? "आधिकारिक कदम देखें" : "CONTINUE TO OFFICIAL HANDOFF"} →</PrimaryButton><button className="app-back !mt-0" onClick={()=>setStage("draft")}>← {t("j.back")}</button></div></>}

    {stage === "final" && result?.official_step && <><p className="app-eyebrow">[ OFFICIAL HANDOFF / 04 ]</p><h1 className="app-title">{t("j.finalTitle")}</h1><Card className="app-dots"><p className="app-section-label">[ WHAT TO DO ]</p><h2 className="text-2xl font-medium">{text(result.official_step.label,locale)}</h2><p className="deadline-inline">{result.deadline?.due_date}</p></Card><div className="notice-boundary"><p className="app-section-label">[ IMPORTANT BOUNDARY ]</p><p className="app-body font-medium">{t("j.finalBoundary")}</p><p className="app-body mt-2">{t("j.finalInstruction")}</p></div><div className="final-actions"><a className="app-primary" href={OFFICIAL_EFILING_PORTAL_URL} target="_blank" rel="noopener noreferrer">{t("j.continuePortal")}</a><button onClick={async()=>{await navigator.clipboard.writeText(draft);setCopied(true)}}>{copied?t("j.finalCopied"):t("j.finalCopy")}</button></div><button className="app-back" onClick={()=>setStage("review")}>← {t("j.back")}</button></>}

    {stage === "refusal" && result && <><p className="app-eyebrow">[ SAFE STOP ]</p><h1 className="app-title">{text(result.headline,locale)}</h1><div className="refusal-layout"><Card><p className="app-section-label">[ WHY ]</p><p className="app-body">{text(result.why,locale)}</p></Card><Card><p className="app-section-label">[ SUGGESTION ]</p><p className="app-body">{text(result.suggestion,locale)}</p></Card><Card>{result.official_links?.map(link=><a key={link.url} className="app-text-action block mb-3" href={verifiedIncomeTaxUrl(link.url)} target="_blank" rel="noopener noreferrer">{text(link.label,locale)} ↗</a>)}</Card></div><button className="app-back" onClick={()=>setStage("requests")}>← {locale === "hi" ? "फिर से जांचें" : "REVIEW REQUESTS AGAIN"}</button></>}
  </div>;
}
