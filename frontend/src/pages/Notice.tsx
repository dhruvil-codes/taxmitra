import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, NoticeCard } from "../lib";
import { CapabilityBadge, CapabilityBoundary } from "../components/UniversalWorkflow";
import { NoticeFactsCard, PrimaryButton, ScreenFrame, WorkflowLayout } from "../components";

export default function Notice() {
  const { id = "" } = useParams();
  const { locale } = useI18n();
  const [notice, setNotice] = useState<NoticeCard | null>(null);
  const [route, setRoute] = useState<Awaited<ReturnType<typeof api.noticeWorkflow>> | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => { if (id) Promise.all([api.notice(id), api.noticeWorkflow(id)]).then(([loaded, routed]) => { setNotice(loaded); setRoute(routed); }).catch(() => setError(true)); }, [id]);
  if (error) return <div className="app-page"><div className="app-empty" role="alert">We could not load this communication.</div></div>;
  if (!notice || !route) return <div className="app-page"><div className="app-loading">LOADING NOTICE DETAILS...</div></div>;
  const capability = route.classification.capability ?? "SAFE_STOP";
  const title = route.workflow?.title[locale] ?? route.workflow?.title.en ?? notice.title[locale] ?? notice.title.en;
  return <WorkflowLayout currentStep={0} notice={notice} noticeId={id}><NoticeFactsCard notice={notice} /><ScreenFrame whereAmI="Step 01 · Understand" whatDoesThisMean={title} whatDoINeedToDo="Review what was identified, the original communication, confidence, and any deadline before choosing the next step." statusBadge={<CapabilityBadge capability={capability} locale={locale} />} primaryAction={<PrimaryButton href={`/notices/${id}/journey`}>{capability === "SAFE_STOP" ? "Review safe boundary" : "Continue"} →</PrimaryButton>} secondaryAction={<Link to="/notices" className="app-back-link">← All notices</Link>}><div className="space-y-5"><div className="universal-section"><p className="app-section-label">[ WHAT WE FOUND ]</p><p className="app-lead">{notice.official_text || route.classification.reason}</p><div className="workflow-contract-meta mt-4"><span>{Math.round(route.classification.confidence * 100)}% confidence</span><span>{route.classification.grounding_status}</span><span>{notice.section || "Section not identified"}</span></div></div>{capability === "SAFE_STOP" && <CapabilityBoundary capability="SAFE_STOP" reason={route.classification.reason} nextSteps={["Review the deadline in the original communication.", "Consult a qualified tax professional where appropriate."]} locale={locale} />}</div></ScreenFrame></WorkflowLayout>;
}
