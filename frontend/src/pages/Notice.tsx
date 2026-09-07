import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, NoticeCard } from "../lib";
import { CapabilityBadge, CapabilityBoundary, ContractExplanation } from "../components/UniversalWorkflow";
import { NoticeFactsCard, PrimaryButton, ScreenFrame, WorkflowLayout } from "../components";

export default function Notice() {
  const { id = "" } = useParams();
  const { locale } = useI18n();
  const [notice, setNotice] = useState<NoticeCard | null>(null);
  const [route, setRoute] = useState<Awaited<ReturnType<typeof api.noticeWorkflow>> | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (id) Promise.all([api.notice(id), api.noticeWorkflow(id)]).then(([loaded, routed]) => { setNotice(loaded); setRoute(routed); }).catch(() => setError(true));
  }, [id]);

  if (error) return <div className="app-page"><div className="app-empty" role="alert">We could not load this communication.</div></div>;
  if (!notice || !route) return <div className="app-page"><div className="app-loading">LOADING NOTICE DETAILS...</div></div>;

  const capability = route.classification.capability ?? "SAFE_STOP";
  const title = route.workflow?.title[locale] ?? route.workflow?.title.en ?? notice.title[locale] ?? notice.title.en;
  const requests = route.contract?.requests ?? [];
  const nextSteps = ["Review the communication and its deadline.", "Use the official Income Tax e-Filing portal for any required action."];
  return <WorkflowLayout currentStep={0} notice={notice} noticeId={id}>
    <NoticeFactsCard notice={notice} />
    <ScreenFrame whereAmI="Step 01 · Understand" whatDoesThisMean={title} whatDoINeedToDo="Review what was identified, the original communication, and any deadline before choosing the next step." statusBadge={<CapabilityBadge capability={capability} locale={locale} />} primaryAction={<PrimaryButton href={capability === "SAFE_STOP" ? `/notices/${id}/journey` : `/notices/${id}/journey?step=questions`}>{capability === "SAFE_STOP" ? "Review safe boundary" : "Continue"} →</PrimaryButton>} secondaryAction={<Link to="/notices" className="app-back-link">← All notices</Link>}>
      <div className="space-y-5">
        <ContractExplanation capability={capability} title={title} reason={route.classification.reason} notice={notice} requests={requests} nextSteps={nextSteps} originalText={notice.official_text} locale={locale} />
        {capability === "SAFE_STOP" && <CapabilityBoundary capability="SAFE_STOP" reason={route.classification.reason} nextSteps={nextSteps} locale={locale} />}
      </div>
    </ScreenFrame>
  </WorkflowLayout>;
}
