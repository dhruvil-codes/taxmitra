import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, Explanation, NoticeCard as NoticeCardT } from "../lib";
import {
  CitationChips,
  NoticeFactsCard,
  PrimaryButton,
  SavedGuidanceBadge,
  ScreenFrame,
  WhyDrawer,
  WorkflowLayout,
} from "../components";

export default function Notice() {
  const { id } = useParams<{ id: string }>();
  const { t, locale } = useI18n();
  const [notice, setNotice] = useState<NoticeCardT | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.notice(id).then(setNotice).catch(() => setError(true));
    api.explanation(id, locale).then(setExplanation).catch(() => setExplanation(null));
  }, [id, locale]);

  if (error) {
    return (
      <div className="workflow-main">
        <div className="app-empty">
          <p className="app-section-label">NOTICE UNAVAILABLE</p>
          <p>We could not load this notice. Please return to your notices index.</p>
          <Link className="app-back-link mt-4" to="/notices">← Back to notices</Link>
        </div>
      </div>
    );
  }

  if (!notice) {
    return (
      <div className="workflow-main">
        <div className="app-loading">LOADING NOTICE DETAILS...</div>
      </div>
    );
  }

  if (notice.section.replace(/\s/g, "").startsWith("142(1)")) {
    return <Navigate to={`/notices/${id}/scrutiny`} replace />;
  }

  const whereAmI = locale === "hi" ? "चरण 01 / 06 · नोटिस समझें" : "Step 01 of 06 · Understand Your Notice";
  const whatDoesThisMean = notice.title[locale] ?? notice.title.en;
  const whatDoINeedToDo =
    locale === "hi"
      ? "विभाग ने आपके रिटर्न और तृतीय-पक्ष डेटा में विसंगति पाई है। उत्तर का प्रारूप तैयार करने के लिए अपने रिकॉर्ड की पुष्टि करें।"
      : "The Department proposed an adjustment to your reported income based on third-party reporting. Confirm your records to prepare an official response.";
  const whatHappensNext =
    locale === "hi"
      ? "अगला कदम: हम आपसे 3 सरल प्रश्न पूछेंगे कि क्या यह आय आपके रिटर्न में पहले से शामिल थी।"
      : "Next step: Answer 3 simple questions to verify whether this income was reported in your return.";

  return (
    <WorkflowLayout currentStep={0} notice={notice} noticeId={id}>
      <NoticeFactsCard notice={notice} />

      <ScreenFrame
        whereAmI={whereAmI}
        whatDoesThisMean={whatDoesThisMean}
        whatDoINeedToDo={whatDoINeedToDo}
        statusBadge={
          <SavedGuidanceBadge
            show={explanation?.demo_mode || explanation?.source === "static"}
            verified={
              Boolean(explanation?.citations?.length) &&
              explanation!.citations.every((c) => c.verification_status === "VERIFIED_OFFICIAL")
            }
          />
        }
        primaryAction={
          <PrimaryButton href={`/notices/${id}/journey`}>
            {locale === "hi" ? "मार्गदर्शित प्रश्नों पर आगे बढ़ें" : "Continue to Guided Questions"} →
          </PrimaryButton>
        }
        secondaryAction={
          <Link to="/notices" className="app-back-link">
            ← {locale === "hi" ? "सभी नोटिस" : "All notices"}
          </Link>
        }
        whatHappensNext={whatHappensNext}
      >
        <div className="screen-task-content space-y-4">
          {/* Plain Meaning */}
          <div className="p-5 bg-white border border-slate-200">
            <h2 className="text-xs font-bold text-blue-600 tracking-wider uppercase mb-2">
              {locale === "hi" ? "सरल भाषा में व्याख्या" : "PLAIN-LANGUAGE SUMMARY"}
            </h2>
            <p className="text-base text-slate-900 leading-relaxed font-medium">
              {explanation?.content.plain_language ?? "Loading explanation..."}
            </p>
          </div>

          {/* What This Does NOT Mean */}
          <div className="p-5 bg-slate-50 border border-slate-200 border-l-4 border-l-slate-700">
            <h2 className="text-xs font-bold text-slate-700 tracking-wider uppercase mb-2">
              {locale === "hi" ? "इसका क्या अर्थ नहीं है" : "WHAT THIS DOES NOT MEAN"}
            </h2>
            <p className="text-sm text-slate-700 leading-relaxed">
              {explanation?.content.what_this_does_not_mean ??
                "This intimation is not a penalty notice or a criminal proceeding. It is a proposed computational adjustment."}
            </p>
          </div>

          {/* Expandable Why Drawer: Possible Reasons, Official Notice, Citations, 2025 Transition Context */}
          <WhyDrawer title={locale === "hi" ? "विवरण और आधिकारिक स्रोत देखें (वैकल्पिक)" : "View detailed reasons & official statutory sources (Optional)"}>
            <div className="space-y-4">
              {explanation && explanation.content.possible_reasons.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-slate-900 tracking-wider uppercase mb-2">
                    {locale === "hi" ? "विसंगति के संभावित कारण" : "POSSIBLE REASONS FOR MISMATCH"}
                  </h3>
                  <ol className="list-decimal pl-5 space-y-1.5 text-sm text-slate-700">
                    {explanation.content.possible_reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ol>
                </div>
              )}

              {notice.official_text && (
                <div className="pt-3 border-t border-slate-200">
                  <h3 className="text-xs font-bold text-slate-900 tracking-wider uppercase mb-2">
                    {locale === "hi" ? "आधिकारिक नोटिस पाठ (DIN)" : "OFFICIAL NOTICE TEXT (DOCUMENT IDENTIFICATION NUMBER)"}
                  </h3>
                  <pre className="text-xs text-slate-800 bg-slate-100 p-3 rounded-none overflow-x-auto whitespace-pre-wrap font-mono border border-slate-200 max-h-60 overflow-y-auto">
                    {notice.official_text}
                  </pre>
                </div>
              )}

              {/* Statutory Note on Income-tax Act, 1961 & 2025 Transition */}
              <div className="pt-3 border-t border-slate-200 bg-blue-50/50 p-3 border border-blue-100">
                <h3 className="text-xs font-bold text-blue-900 tracking-wider uppercase mb-1">
                  STATUTORY APPLICABILITY & ACT 2025 TRANSITION NOTE
                </h3>
                <p className="text-xs text-slate-700 leading-relaxed">
                  Notice issued under Section 143(1)(a) of the Income-tax Act, 1961 for Assessment Year {notice.assessment_year || "2025-26"}. Under Section 536 transitional savings provisions of the Income Tax Act, 2025, proceedings and intimations for earlier tax years continue under the 1961 Act framework via the unified electronic e-filing portal.
                </p>
              </div>

              {explanation && (
                <div className="pt-3 border-t border-slate-200">
                  <CitationChips citations={explanation.citations} />
                </div>
              )}
            </div>
          </WhyDrawer>
        </div>
      </ScreenFrame>
    </WorkflowLayout>
  );
}
