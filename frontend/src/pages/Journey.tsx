import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, Question, ResolveResult, formatINR, OFFICIAL_EFILING_PORTAL_URL, store, NoticeCard } from "../lib";
import {
  PrimaryButton,
  SecondaryButton,
  ScreenFrame,
  WorkflowLayout,
  WhyDrawer,
} from "../components";

type Phase = "questions" | "checklist" | "draft" | "review" | "final";

export default function Journey() {
  const { id = "" } = useParams();
  const { locale, t } = useI18n();

  const [phase, setPhase] = useState<Phase>("questions");
  const [notice, setNotice] = useState<NoticeCard | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [qIndex, setQIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>(() => store.answers(id));
  const [result, setResult] = useState<ResolveResult | null>(null);
  const [draft, setDraft] = useState("");
  const [copied, setCopied] = useState(false);
  const [docStatuses, setDocStatuses] = useState<Record<string, "have" | "need_to_find" | "dont_have" | "not_sure">>({});
  const [reviewApproved, setReviewApproved] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.notice(id).then(setNotice).catch(() => null);
    api.questions(id, locale).then((res) => {
      setQuestions(res.questions);
      const firstUnanswered = res.questions.findIndex((q) => !answers[q.id]);
      setQIndex(firstUnanswered === -1 ? 0 : firstUnanswered);
    });
  }, [id, locale]);

  const handleAnswer = (optionId: string) => {
    const q = questions[qIndex];
    const updated = { ...answers, [q.id]: optionId };
    setAnswers(updated);
    store.setAnswers(id, updated);

    if (qIndex < questions.length - 1) {
      setQIndex(qIndex + 1);
    } else {
      api.resolve(id, updated).then((res) => {
        setResult(res);
        const initialDraft = store.draft(id) || res.draft || "";
        setDraft(initialDraft);
        store.setDraft(id, initialDraft);
        if (res.checklist) {
          const initDoc: Record<string, "have" | "need_to_find" | "dont_have" | "not_sure"> = {};
          res.checklist.forEach((item) => {
            initDoc[item.id] = "need_to_find";
          });
          setDocStatuses(initDoc);
        }
        setPhase("checklist");
      });
    }
  };

  const setDocStatus = (docId: string, status: "have" | "need_to_find" | "dont_have" | "not_sure") => {
    setDocStatuses((prev) => ({ ...prev, [docId]: status }));
  };

  const copyDraft = () => {
    navigator.clipboard.writeText(draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadAsTxt = () => {
    const blob = new Blob([draft], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tax-mitra-response-${id}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadAsMarkdown = () => {
    if (!draft || !notice) return;
    const md = `# Tax Mitra Response Draft\n\n**Notice:** ${notice.section} · ${notice.title[locale] ?? notice.title.en}\n**Assessment Year:** ${notice.assessment_year}\n**Reference DIN:** ${notice.official_reference || "DEMO"}\n\n---\n\n${draft}\n`;
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tax-mitra-response-${id}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadAsPdf = () => {
    if (!draft || !notice) return;
    const printContent = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Tax Mitra Response Draft</title><style>body { font-family: 'Inter', sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #101115; } h1 { border-bottom: 2px solid #000; padding-bottom: 8px; font-size: 20px; } .meta { color: #555; margin-bottom: 24px; font-size: 13px; } .draft { white-space: pre-wrap; font-size: 14px; } .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #ccc; font-size: 11px; color: #777; }</style></head><body><h1>Tax Mitra Formal Response Draft</h1><div class="meta"><p><strong>Notice:</strong> ${notice.section} · ${notice.title[locale] ?? notice.title.en}</p><p><strong>Assessment Year:</strong> ${notice.assessment_year}</p><p><strong>Reference:</strong> ${notice.official_reference || "DEMO"}</p></div><div class="draft">${draft}</div><div class="footer"><p>This document is prepared via Tax Mitra for citizen filing on incometax.gov.in. Tax Mitra does not file on your behalf.</p></div></body></html>`;
    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(printContent);
      printWindow.document.close();
      printWindow.print();
    }
  };

  const stepIndex: 0 | 1 | 2 | 3 | 4 | 5 =
    phase === "questions" ? 1 : phase === "checklist" ? 2 : phase === "draft" ? 3 : phase === "review" ? 4 : 5;

  const currentQ = questions[qIndex];
  const totalQ = questions.length || 3;

  return (
    <WorkflowLayout currentStep={stepIndex} notice={notice} noticeId={id}>
      {/* =========================================================================
          STEP 02: QUESTIONS
         ========================================================================= */}
      {phase === "questions" && (
        <ScreenFrame
          whereAmI={
            locale === "hi"
              ? `चरण 02 / 06 · प्रश्न ${qIndex + 1} / ${totalQ}`
              : `Step 02 of 06 · Question ${qIndex + 1} of ${totalQ}`
          }
          whatDoesThisMean={
            currentQ?.text ||
            (locale === "hi" ? "क्या रिपोर्ट की गई राशि आपके रिकॉर्ड से मेल खाती है?" : "Does the Department's reported amount match your records?")
          }
          whatDoINeedToDo={
            currentQ?.help ||
            (locale === "hi" ? "अपने बैंक विवरण या दाखिल रिटर्न के अनुसार उचित विकल्प चुनें।" : "Select Yes, No, or Not Sure based on your actual bank statements and filed return.")
          }
          primaryAction={null}
          secondaryAction={
            <div className="flex items-center gap-3">
              {qIndex > 0 ? (
                <SecondaryButton onClick={() => setQIndex(qIndex - 1)}>
                  ← {locale === "hi" ? "पिछला प्रश्न" : "Previous Question"}
                </SecondaryButton>
              ) : (
                <Link to={`/notices/${id}`} className="app-back-link">
                  ← {locale === "hi" ? "नोटिस विवरण" : "Notice Details"}
                </Link>
              )}
            </div>
          }
          whatHappensNext={
            qIndex < totalQ - 1
              ? (locale === "hi" ? `अगला कदम: प्रश्न ${qIndex + 2} / ${totalQ}` : `Next step: Question ${qIndex + 2} of ${totalQ}`)
              : (locale === "hi" ? "अगला कदम: आपके उत्तरों के आधार पर आवश्यक दस्तावेज़ों की सूची।" : "Next step: Evidence and document checklist tailored to your answers.")
          }
        >
          {currentQ && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {currentQ.options.map((opt) => {
                  const isSelected = answers[currentQ.id] === opt.id;
                  return (
                    <button
                      key={opt.id}
                      onClick={() => handleAnswer(opt.id)}
                      className={`p-4 text-center border font-semibold text-base transition-all min-h-[56px] flex items-center justify-center ${
                        isSelected
                          ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                          : "bg-white text-slate-900 border-slate-300 hover:border-slate-900"
                      }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>

              {currentQ.help && (
                <WhyDrawer title={locale === "hi" ? "यह प्रश्न क्यों पूछा जा रहा है?" : "Why is this question asked?"}>
                  <p className="text-sm text-slate-700 leading-relaxed">
                    {currentQ.help}
                  </p>
                </WhyDrawer>
              )}
            </div>
          )}
        </ScreenFrame>
      )}

      {/* =========================================================================
          STEP 03: DOCUMENTS
         ========================================================================= */}
      {phase === "checklist" && result && (
        <ScreenFrame
          whereAmI={locale === "hi" ? "चरण 03 / 06 · दस्तावेज़ सूची" : "Step 03 of 06 · Document Checklist"}
          whatDoesThisMean={result.path?.headline[locale] ?? result.path?.headline.en ?? "Supporting Documents Needed"}
          whatDoINeedToDo={
            locale === "hi"
              ? "प्रत्येक दस्तावेज़ की स्थिति चिह्नित करें (मेरे पास है / ढूंढना है / नहीं है)।"
              : "Mark the availability of each document so that missing evidence is clearly identified."
          }
          primaryAction={
            <PrimaryButton onClick={() => setPhase("draft")}>
              {locale === "hi" ? "उत्तर का प्रारूप तैयार करें" : "Prepare Draft Response"} →
            </PrimaryButton>
          }
          secondaryAction={
            <SecondaryButton onClick={() => setPhase("questions")}>
              ← {locale === "hi" ? "प्रश्नों पर वापस जाएं" : "Back to Questions"}
            </SecondaryButton>
          }
          whatHappensNext={
            locale === "hi"
              ? "अगला कदम: आपके उत्तरों और दस्तावेज़ों के आधार पर संपादन योग्य उत्तर प्रारूप।"
              : "Next step: Editable statutory response draft pre-filled with your position."
          }
        >
          <div className="space-y-4">
            {result.checklist && result.checklist.length > 0 ? (
              result.checklist.map((item) => {
                const currentStatus = docStatuses[item.id] || "need_to_find";
                return (
                  <div key={item.id} className="evidence-item-card">
                    <div className="evidence-header">
                      <h3 className="evidence-name">{item.title[locale] ?? item.title.en}</h3>
                      <span className={`evidence-status-pill ${currentStatus === "have" ? "bg-emerald-100 text-emerald-800" : currentStatus === "dont_have" ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"}`}>
                        {currentStatus === "have" ? "Have it" : currentStatus === "dont_have" ? "Don't have" : currentStatus === "not_sure" ? "Not sure" : "Need to find"}
                      </span>
                    </div>
                    <p className="evidence-reason">{item.why_needed[locale] ?? item.why_needed.en}</p>
                    <div className="evidence-status-actions-row">
                      <button
                        type="button"
                        onClick={() => setDocStatus(item.id, "have")}
                        className={`status-choice-btn ${currentStatus === "have" ? "is-have" : ""}`}
                      >
                        ✓ {locale === "hi" ? "मेरे पास है" : "Have it"}
                      </button>
                      <button
                        type="button"
                        onClick={() => setDocStatus(item.id, "need_to_find")}
                        className={`status-choice-btn ${currentStatus === "need_to_find" ? "is-need-find" : ""}`}
                      >
                        🔍 {locale === "hi" ? "ढूंढना है" : "Need to find it"}
                      </button>
                      <button
                        type="button"
                        onClick={() => setDocStatus(item.id, "dont_have")}
                        className={`status-choice-btn ${currentStatus === "dont_have" ? "is-dont-have" : ""}`}
                      >
                        ✗ {locale === "hi" ? "नहीं है" : "Don't have it"}
                      </button>
                      <button
                        type="button"
                        onClick={() => setDocStatus(item.id, "not_sure")}
                        className={`status-choice-btn ${currentStatus === "not_sure" ? "is-not-sure" : ""}`}
                      >
                        ? {locale === "hi" ? "पक्का नहीं" : "Not sure"}
                      </button>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-slate-600">No specific documents required for this notice type.</p>
            )}

            {result.path?.guidance && (
              <WhyDrawer title={locale === "hi" ? "विस्तृत कानूनी मार्गदर्शन देखें" : "View statutory guidance reasoning"}>
                <p className="text-sm text-slate-700 leading-relaxed">
                  {result.path.guidance[locale] ?? result.path.guidance.en}
                </p>
              </WhyDrawer>
            )}
          </div>
        </ScreenFrame>
      )}

      {/* =========================================================================
          STEP 04: RESPONSE DRAFT
         ========================================================================= */}
      {phase === "draft" && (
        <ScreenFrame
          whereAmI={locale === "hi" ? "चरण 04 / 06 · उत्तर प्रारूप" : "Step 04 of 06 · Response Draft"}
          whatDoesThisMean={locale === "hi" ? "आपके उत्तरों पर आधारित वैधानिक उत्तर प्रारूप" : "Formal Statutory Response Draft"}
          whatDoINeedToDo={
            locale === "hi"
              ? "प्रारूप की समीक्षा करें। आप सीधे नीचे दिए गए टेक्स्ट बॉक्स में बदलाव या संपादन कर सकते हैं।"
              : "Review your draft response. You can freely edit or refine every sentence in the text area below."
          }
          primaryAction={
            <PrimaryButton onClick={() => setPhase("review")}>
              {locale === "hi" ? "कार्यकारी समीक्षा पर जाएं" : "Continue to Executive Review"} →
            </PrimaryButton>
          }
          secondaryAction={
            <SecondaryButton onClick={() => setPhase("checklist")}>
              ← {locale === "hi" ? "दस्तावेज़ों पर वापस जाएं" : "Back to Documents"}
            </SecondaryButton>
          }
          whatHappensNext={
            locale === "hi"
              ? "अगला कदम: आधिकारिक पोर्टल पर जाने से पहले अंतिम समीक्षा और मानव अनुमोदन।"
              : "Next step: Executive safety check and explicit human approval before portal instructions."
          }
        >
          <div className="space-y-4">
            <div className="p-4 bg-slate-50 border border-slate-200 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-slate-600 uppercase tracking-wider">TAXPAYER FACT CHECK</p>
                <p className="text-xs text-slate-700 mt-0.5">
                  Pre-filled using official Income Tax Department response templates. Facts supplied by you are preserved.
                </p>
              </div>
              <button
                type="button"
                onClick={copyDraft}
                className="text-xs font-bold text-blue-600 hover:text-blue-800 border border-blue-200 bg-white px-3 py-1.5"
              >
                {copied ? "✓ Copied" : "Copy Draft"}
              </button>
            </div>

            <div>
              <label htmlFor="response-draft-editor" className="sr-only">Response draft editor</label>
              <textarea
                id="response-draft-editor"
                value={draft}
                onChange={(e) => {
                  setDraft(e.target.value);
                  store.setDraft(id, e.target.value);
                }}
                rows={14}
                className="w-full p-4 font-mono text-sm leading-relaxed border border-slate-300 bg-white text-slate-900 focus:border-blue-600 focus:outline-none"
                placeholder="Your response draft appears here..."
              />
            </div>
          </div>
        </ScreenFrame>
      )}

      {/* =========================================================================
          STEP 05: REVIEW & HUMAN APPROVAL GATE
         ========================================================================= */}
      {phase === "review" && (
        <ScreenFrame
          whereAmI={locale === "hi" ? "चरण 05 / 06 · अंतिम समीक्षा" : "Step 05 of 06 · Executive Review"}
          whatDoesThisMean={locale === "hi" ? "अंतिम उत्तर की समीक्षा और अनुमोदन" : "Executive Pre-Filing Review"}
          whatDoINeedToDo={
            locale === "hi"
              ? "सुनिश्चित करें कि सभी विवरण सही हैं और पोर्टल पर आगे बढ़ने के लिए अपनी स्पष्ट सहमति दें।"
              : "Verify all components below and provide explicit approval to proceed to official filing."
          }
          primaryAction={
            <PrimaryButton
              disabled={!reviewApproved}
              onClick={() => setPhase("final")}
            >
              {locale === "hi" ? "अनुमोदित करें और पोर्टल पर जाएं" : "Approve & Continue to Official Portal"} →
            </PrimaryButton>
          }
          secondaryAction={
            <SecondaryButton onClick={() => setPhase("draft")}>
              ← {locale === "hi" ? "ड्राफ्ट संपादित करें" : "Edit Draft"}
            </SecondaryButton>
          }
          whatHappensNext={
            locale === "hi"
              ? "अगला कदम: incometax.gov.in पर उत्तर दाखिल करने के लिए चरण-दर-चरण निर्देश।"
              : "Next step: Step-by-step handoff to submit your approved draft on incometax.gov.in."
          }
        >
          <div className="executive-review-card space-y-6">
            <div className="review-items-list">
              <div className="review-checklist-item">
                <span className="review-item-name">Notice Section & Assessment Year</span>
                <span className="review-item-status">{notice?.section} · AY {notice?.assessment_year || "2025-26"} ✓</span>
              </div>
              <div className="review-checklist-item">
                <span className="review-item-name">Guided Questionnaire</span>
                <span className="review-item-status">{totalQ}/{totalQ} Answered ✓</span>
              </div>
              <div className="review-checklist-item">
                <span className="review-item-name">Evidence Document Readiness</span>
                <span className="review-item-status">
                  {Object.values(docStatuses).filter((s) => s === "have").length}/
                  {Object.keys(docStatuses).length || 1} Ready
                </span>
              </div>
              <div className="review-checklist-item">
                <span className="review-item-name">Formal Statutory Draft</span>
                <span className="review-item-status">{draft.length > 0 ? "Completed & Editable ✓" : "Pending"}</span>
              </div>
              <div className="review-checklist-item">
                <span className="review-item-name">Authoritative Statutory Grounding</span>
                <span className="review-item-status">Verified Official Corpus ✓</span>
              </div>
            </div>

            {/* Explicit Human Approval Gate */}
            <div className="approval-gate-box">
              <label className="approval-gate-label">
                <input
                  type="checkbox"
                  checked={reviewApproved}
                  onChange={(e) => setReviewApproved(e.target.checked)}
                />
                <span>
                  {locale === "hi"
                    ? "मैंने response draft, आवश्यक दस्तावेज़ों और आधिकारिक स्रोतों की समीक्षा कर ली है। मैं आधिकारिक आयकर पोर्टल पर स्वयं उत्तर जमा करने के लिए आगे बढ़ने की अनुमति देता/देती हूँ।"
                    : "I have reviewed the response draft, evidence checklist, and statutory citations. I approve moving forward to submit this response directly on the official Income Tax e-Filing portal."}
                </span>
              </label>
            </div>
          </div>
        </ScreenFrame>
      )}

      {/* =========================================================================
          STEP 06: ACT ON OFFICIAL PORTAL
         ========================================================================= */}
      {phase === "final" && result?.official_step && (
        <ScreenFrame
          whereAmI={locale === "hi" ? "चरण 06 / 06 · आधिकारिक पोर्टल" : "Step 06 of 06 · Submit on Official Portal"}
          whatDoesThisMean={locale === "hi" ? "आधिकारिक ई-फाइलिंग पोर्टल पर जमा करें" : "Submit Your Response on incometax.gov.in"}
          whatDoINeedToDo={
            locale === "hi"
              ? "अपना ड्राफ्ट डाउनलोड करें या कॉपी करें, और आधिकारिक पोर्टल पर 'Pending Actions' में जमा करें।"
              : "Download or copy your approved draft, log in to the official Income Tax portal, and submit in Pending Actions."
          }
          primaryAction={
            <PrimaryButton href={OFFICIAL_EFILING_PORTAL_URL}>
              {locale === "hi" ? "आधिकारिक ई-फाइलिंग पोर्टल खोलें" : "Open Income Tax e-Filing Portal"} ↗
            </PrimaryButton>
          }
          secondaryAction={
            <SecondaryButton onClick={() => setPhase("review")}>
              ← {locale === "hi" ? "समीक्षा पर वापस जाएं" : "Back to Review"}
            </SecondaryButton>
          }
          whatHappensNext={
            locale === "hi"
              ? "अंतिम स्थिति: आधिकारिक पोर्टल पावती (Acknowledgement) संख्या को सुरक्षित रखें।"
              : "Final: Keep your official e-Filing submission acknowledgement receipt for your tax records."
          }
        >
          <div className="space-y-6">
            {/* Step-by-Step Instructions */}
            <div className="p-5 bg-white border border-slate-200">
              <h3 className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-3">
                {locale === "hi" ? "ई-फाइलिंग पोर्टल पर कैसे जमा करें" : "OFFICIAL PORTAL SUBMISSION STEPS"}
              </h3>
              <ol className="list-decimal pl-5 space-y-2 text-sm text-slate-800 font-medium">
                <li>Log in to your account at <strong>incometax.gov.in</strong> using your PAN and password.</li>
                <li>Navigate to the <strong>Pending Actions</strong> tab in the top navigation bar.</li>
                <li>Click on <strong>e-Proceedings</strong> and locate your notice DIN ({notice?.official_reference || "N-2026-001"}).</li>
                <li>Select <strong>Submit Response</strong> and paste your approved text or upload supporting documents.</li>
                <li>Verify using Aadhaar OTP / EVC and note the official acknowledgement number.</li>
              </ol>
            </div>

            {/* Download Options */}
            <div className="p-5 bg-slate-50 border border-slate-200">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                {locale === "hi" ? "उत्तर का प्रारूप डाउनलोड करें" : "DOWNLOAD APPROVED RESPONSE"}
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={downloadAsTxt}
                  className="p-3 bg-white border border-slate-300 text-slate-900 font-semibold text-sm hover:border-slate-900"
                >
                  Download .TXT
                </button>
                <button
                  type="button"
                  onClick={downloadAsMarkdown}
                  className="p-3 bg-white border border-slate-300 text-slate-900 font-semibold text-sm hover:border-slate-900"
                >
                  Download .MD
                </button>
                <button
                  type="button"
                  onClick={downloadAsPdf}
                  className="p-3 bg-white border border-slate-300 text-slate-900 font-semibold text-sm hover:border-slate-900"
                >
                  Print / Save PDF
                </button>
              </div>
            </div>

            {/* Boundary Reassurance */}
            <div className="p-4 bg-blue-50/60 border border-blue-200 text-xs text-blue-900 leading-relaxed">
              <strong>STATUTORY BOUNDARY:</strong> Tax Mitra has not submitted this response to the Government of India. No taxpayer credentials or confidential return data are transmitted. Official filing remains 100% under citizen control on incometax.gov.in.
            </div>
          </div>
        </ScreenFrame>
      )}
    </WorkflowLayout>
  );
}
