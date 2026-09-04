import { ReactNode, useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useI18n } from "./i18n";
import { Citation, Locale, NoticeCard } from "./lib";

export function DisclaimerBanner() {
  const { t } = useI18n();
  return (
    <div className="app-disclaimer">
      <span className="disclaimer-badge">PUBLIC PROTOTYPE</span>
      <span>{t("banner")} · {t("appDisclaimer")}</span>
    </div>
  );
}

export function LanguageSelector() {
  const { locale, setLocale, t } = useI18n();
  return (
    <label className="app-language">
      <span className="sr-only">{t("lang.label")}</span>
      <select
        aria-label={t("lang.label")}
        value={locale}
        onChange={(e) => setLocale(e.target.value as Locale)}
      >
        <option value="en">English</option>
        <option value="hi">हिन्दी</option>
      </select>
    </label>
  );
}

export function Header() {
  const { t } = useI18n();
  const { pathname } = useLocation();
  const isHome = pathname === "/";
  return (
    <header className="app-header">
      <Link to="/" className="app-brand" aria-current={isHome ? "page" : undefined}>
        <span className="app-brand-mark">त</span>
        <div className="app-brand-text">
          <strong>{t("app.name")}</strong>
          <small>INDEPENDENT TAXPAYER PROTOTYPE</small>
        </div>
      </Link>
      <nav aria-label="Primary" className="header-nav">
        <Link to="/notices">NOTICES</Link>
        <Link to="/upload">UPLOAD PDF</Link>
        <a href="/#trust">SAFETY & PRIVACY</a>
      </nav>
      <div className="header-actions">
        <LanguageSelector />
      </div>
    </header>
  );
}

export interface WorkflowStepItem {
  id: string;
  num: string;
  label: Record<string, string>;
}

export const WORKFLOW_STEPS: WorkflowStepItem[] = [
  { id: "understand", num: "01", label: { en: "Understand", hi: "समझें" } },
  { id: "questions", num: "02", label: { en: "Questions", hi: "सवाल" } },
  { id: "documents", num: "03", label: { en: "Documents", hi: "दस्तावेज़" } },
  { id: "response", num: "04", label: { en: "Response", hi: "उत्तर" } },
  { id: "review", num: "05", label: { en: "Review", hi: "समीक्षा" } },
  { id: "act", num: "06", label: { en: "Act", hi: "कार्रवाई" } },
];

export function WorkflowLayout({
  currentStep,
  notice,
  noticeId,
  onStepSelect,
  children,
}: {
  currentStep: 0 | 1 | 2 | 3 | 4 | 5;
  notice?: NoticeCard | null;
  noticeId?: string;
  onStepSelect?: (step: 0 | 1 | 2 | 3 | 4 | 5) => void;
  children: ReactNode;
}) {
  const { locale } = useI18n();
  const activeStep = WORKFLOW_STEPS[currentStep];

  return (
    <div className="workflow-shell">
      {/* Mobile Compact Progress Bar */}
      <div className="workflow-mobile-bar" aria-label="Workflow progress">
        <div className="mobile-progress-badge">
          <span className="mobile-step-num">{activeStep.num} / 06</span>
          <span className="mobile-step-name">{activeStep.label[locale] ?? activeStep.label.en}</span>
        </div>
        {notice && (
          <span className="mobile-notice-pill">
            {notice.section} · AY {notice.assessment_year || "—"}
          </span>
        )}
      </div>

      {/* Desktop Persistent Left Sidebar Navigation */}
      <aside className="workflow-sidebar" aria-label="Workflow navigation">
        <div className="sidebar-header">
          <p className="sidebar-kicker">TAXPAYER WORKFLOW</p>
          {notice && (
            <div className="sidebar-notice-card">
              <span className="sidebar-section-tag">{notice.section}</span>
              <p className="sidebar-notice-title">{notice.title[locale] ?? notice.title.en}</p>
              <div className="sidebar-notice-meta">
                <span>AY {notice.assessment_year || "—"}</span>
                {notice.due_date && <span>Due: {notice.due_date}</span>}
              </div>
            </div>
          )}
        </div>

        <nav className="sidebar-steps" aria-label="Steps">
          <ol>
            {WORKFLOW_STEPS.map((step, idx) => {
              const isCompleted = idx < currentStep;
              const isCurrent = idx === currentStep;
              const statusClass = isCurrent ? "is-current" : isCompleted ? "is-completed" : "is-upcoming";

              const content = (
                <>
                  <span className="step-indicator" aria-hidden="true">
                    {isCompleted ? "✓" : step.num}
                  </span>
                  <span className="step-label">{step.label[locale] ?? step.label.en}</span>
                  {isCurrent && <span className="current-marker" aria-hidden="true" />}
                </>
              );

              return (
                <li key={step.id} className={`sidebar-step-item ${statusClass}`} aria-current={isCurrent ? "step" : undefined}>
                  {onStepSelect && isCompleted ? (
                    <button
                      type="button"
                      className="step-btn"
                      onClick={() => onStepSelect(idx as 0 | 1 | 2 | 3 | 4 | 5)}
                    >
                      {content}
                    </button>
                  ) : (
                    <div className="step-content">{content}</div>
                  )}
                </li>
              );
            })}
          </ol>
        </nav>

        <div className="sidebar-footer">
          <p className="sidebar-footer-heading">PRINCIPLE</p>
          <p className="sidebar-footer-rule">AI Explains → Rules Decide → Humans Approve</p>
          {noticeId && (
            <Link to="/notices" className="sidebar-exit-link">
              ← Exit to all notices
            </Link>
          )}
        </div>
      </aside>

      {/* Main Content Focused Area */}
      <div className="workflow-main">{children}</div>
    </div>
  );
}

export function Stepper({ current }: { current: 0 | 1 | 2 | 3 | 4 | 5 }) {
  const { locale } = useI18n();
  return (
    <ol className="app-stepper" aria-label="Progress">
      {WORKFLOW_STEPS.map((step, i) => (
        <li
          key={step.id}
          className={i === current ? "is-current" : i < current ? "is-done" : ""}
          aria-current={i === current ? "step" : undefined}
        >
          <span>{i < current ? "✓" : step.num}</span>
          <strong>{step.label[locale] ?? step.label.en}</strong>
        </li>
      ))}
    </ol>
  );
}

export function WorkflowRail({ current = 0 }: { current?: 0 | 1 | 2 | 3 | 4 | 5 }) {
  const { locale } = useI18n();
  const active = WORKFLOW_STEPS[current];
  return (
    <aside className="workflow-rail-legacy" aria-label="Workflow progress">
      <span>{active.num} / 06</span>
      <strong>{active.label[locale] ?? active.label.en}</strong>
    </aside>
  );
}

export function ScreenFrame({
  whereAmI,
  whatDoesThisMean,
  whatDoINeedToDo,
  statusBadge,
  children,
  primaryAction,
  secondaryAction,
  whatHappensNext,
}: {
  whereAmI: string;
  whatDoesThisMean: string;
  whatDoINeedToDo: string;
  statusBadge?: ReactNode;
  children?: ReactNode;
  primaryAction?: ReactNode;
  secondaryAction?: ReactNode;
  whatHappensNext?: string;
}) {
  return (
    <div className="screen-frame">
      {/* 1. WHERE AM I? */}
      <div className="screen-context-bar">
        <span className="screen-context-step">{whereAmI}</span>
        {statusBadge && <div className="screen-status-badge">{statusBadge}</div>}
      </div>

      {/* 2. WHAT DOES THIS MEAN? */}
      <div className="screen-meaning-box">
        <h1 className="screen-main-heading">{whatDoesThisMean}</h1>
      </div>

      {/* 3. WHAT DO I NEED TO DO? */}
      <div className="screen-instruction-box">
        <p className="screen-instruction-text">{whatDoINeedToDo}</p>
      </div>

      {/* Screen Task Content */}
      {children && <div className="screen-body">{children}</div>}

      {/* 4. PRIMARY ACTION & 5. WHAT HAPPENS NEXT? */}
      {(primaryAction || secondaryAction || whatHappensNext) && (
        <div className="screen-action-dock">
          <div className="action-buttons-row">
            {primaryAction}
            {secondaryAction}
          </div>
          {whatHappensNext && (
            <p className="screen-next-hint">
              <strong>NEXT:</strong> {whatHappensNext}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export function GuidedInteraction({
  step,
  title,
  instruction,
  status,
  next,
  back,
  exit,
}: {
  step: string;
  title: string;
  instruction: string;
  status?: string;
  next?: ReactNode;
  back?: ReactNode;
  exit?: ReactNode;
}) {
  return (
    <ScreenFrame
      whereAmI={step}
      whatDoesThisMean={title}
      whatDoINeedToDo={instruction}
      statusBadge={status ? <span className="guided-status-pill">{status}</span> : undefined}
      primaryAction={next}
      secondaryAction={
        <>
          {back}
          {exit}
        </>
      }
    />
  );
}

export function NoticeFactsCard({ notice }: { notice: NoticeCard }) {
  const { locale } = useI18n();
  const na = locale === "hi" ? "इस नोटिस में उपलब्ध नहीं है" : "Not available in this notice";

  return (
    <div className="notice-facts-card" aria-label="Key notice facts">
      <div className="facts-header">
        <span className="facts-kicker">KEY NOTICE FACTS</span>
        <span className="facts-din">{notice.official_reference || na}</span>
      </div>
      <div className="facts-grid">
        <div className="fact-item">
          <span className="fact-label">NOTICE TYPE</span>
          <strong className="fact-value">{notice.section || na}</strong>
        </div>
        <div className="fact-item">
          <span className="fact-label">ASSESSMENT YEAR</span>
          <strong className="fact-value">{notice.assessment_year ? `AY ${notice.assessment_year}` : na}</strong>
        </div>
        <div className="fact-item">
          <span className="fact-label">NOTICE DATE</span>
          <strong className="fact-value">{notice.issue_date || na}</strong>
        </div>
        <div className="fact-item">
          <span className="fact-label">RESPONSE DEADLINE</span>
          <strong className="fact-value fact-deadline">{notice.due_date || na}</strong>
        </div>
        <div className="fact-item">
          <span className="fact-label">CURRENT STATUS</span>
          <div className="fact-value">
            <StatusChip status={notice.status} daysRemaining={notice.days_remaining} />
          </div>
        </div>
      </div>
    </div>
  );
}

export function WhyDrawer({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  return (
    <details className="why-drawer" open={defaultOpen}>
      <summary className="why-summary">
        <span>{title}</span>
        <span className="why-icon" aria-hidden="true">▾</span>
      </summary>
      <div className="why-content">{children}</div>
    </details>
  );
}

export function SavedGuidanceBadge({ show, verified = false }: { show: boolean; verified?: boolean }) {
  const { t } = useI18n();
  if (!show) return null;
  return (
    <span className="app-saved-badge">
      <span className="badge-bullet">●</span>
      {t(verified ? "notice.verifiedSavedGuidance" : "notice.savedGuidance")}
    </span>
  );
}

export function SourcePanel({ citation, onClose }: { citation: Citation | null; onClose: () => void }) {
  const { t } = useI18n();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!citation) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", closeOnEscape);
    closeRef.current?.focus();
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [citation, onClose]);

  if (!citation) return null;
  const verified =
    citation.verification_status === "VERIFIED_OFFICIAL" ||
    citation.verification_state === "Verified" ||
    citation.verification === "verified";

  return (
    <div className="source-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="source-panel" onClick={(e) => e.stopPropagation()}>
        <div className="source-head">
          <div>
            <span className="source-tag">OFFICIAL STATUTORY SOURCE</span>
            <h3>{citation.title}</h3>
            <p className="source-section">{citation.source_name} · {citation.section}</p>
          </div>
          <button ref={closeRef} onClick={onClose} className="source-close" aria-label="Close source">
            ×
          </button>
        </div>
        <p className={`source-verification ${verified ? "is-verified" : ""}`}>
          ● {citation.verification_state ?? (verified ? t("notice.verification.verified") : t("notice.verification.pending"))}
        </p>
        <p className="source-support">{citation.why_supports ?? "This source is linked to the explanation shown."}</p>
        <div className="source-meta-grid">
          <span>Location:</span>
          <b>{citation.page_location || "Section-level source"}</b>
          <span>Applicability:</span>
          <b>{citation.applicability || "Standard"}</b>
          <span>Effective period:</span>
          <b>{citation.effective_period || "Relevant Assessment Year"}</b>
        </div>
        <blockquote className="source-excerpt">{citation.excerpt}</blockquote>
        <div className="source-footer">
          <a href={citation.official_url} target="_blank" rel="noopener noreferrer">
            {t("notice.viewSource")} ↗
          </a>
          <p>{citation.source_name} · accessed {citation.accessed_date}</p>
        </div>
      </div>
    </div>
  );
}

export function CitationChips({ citations }: { citations: Citation[] }) {
  const { t } = useI18n();
  const [open, setOpen] = useState<Citation | null>(null);
  if (!citations.length) return null;

  return (
    <div className="citation-chips-section">
      <p className="citation-kicker">VERIFIED STATUTORY CITATIONS</p>
      <div className="citation-list">
        {citations.map((c, index) => (
          <button key={c.id} onClick={() => setOpen(c)} className="citation-pill">
            <span className="citation-index">{String(index + 1).padStart(2, "0")}</span>
            <span className="citation-title">{c.section || c.title}</span>
            <span className="citation-arrow">↗</span>
          </button>
        ))}
      </div>
      <SourcePanel citation={open} onClose={() => setOpen(null)} />
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`app-card ${className}`}>{children}</section>;
}

export function PrimaryButton({
  children,
  onClick,
  href,
  disabled = false,
  className = "",
}: {
  children: ReactNode;
  onClick?: () => void;
  href?: string;
  disabled?: boolean;
  className?: string;
}) {
  const cls = `app-primary-btn ${className}`.trim();
  if (href) {
    return (
      <a href={href} target={href.startsWith("http") ? "_blank" : undefined} rel="noopener noreferrer" className={cls}>
        {children}
      </a>
    );
  }
  return (
    <button onClick={onClick} className={cls} disabled={disabled}>
      {children}
    </button>
  );
}

export function SecondaryButton({
  children,
  onClick,
  disabled = false,
  className = "",
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button onClick={onClick} className={`app-secondary-btn ${className}`.trim()} disabled={disabled}>
      {children}
    </button>
  );
}

export function StatusChip({ status, daysRemaining }: { status: string; daysRemaining: number | null }) {
  const { t } = useI18n();
  const label =
    daysRemaining === null
      ? ""
      : daysRemaining < 0
        ? t("dash.overdue")
        : daysRemaining === 0
          ? t("dash.dueToday")
          : t("dash.daysLeft", { n: String(daysRemaining) });

  const tone = status === "expired" ? "is-expired" : status === "due_soon" ? "is-due" : "is-open";
  const text =
    status === "expired"
      ? t("dash.overdue")
      : status === "due_soon"
        ? t("dash.dueSoon")
        : t("dash.actionRequired");

  return (
    <div className="status-chip-container">
      <span className={`status-pill ${tone}`}>{text}</span>
      {label && <span className="status-days">{label}</span>}
    </div>
  );
}
