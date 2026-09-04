import { ReactNode, useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useI18n } from "./i18n";
import { Citation, Locale } from "./lib";

export function DisclaimerBanner() {
  const { t } = useI18n();
  return <div className="app-disclaimer">[ PUBLIC BETA ] &nbsp; {t("banner")} · {t("appDisclaimer")}</div>;
}

export function LanguageSelector() {
  const { locale, setLocale, t } = useI18n();
  return (
    <label className="app-language">
      <span className="sr-only">{t("lang.label")}</span>
      <select aria-label={t("lang.label")} value={locale} onChange={(e) => setLocale(e.target.value as Locale)}>
        <option value="en">EN</option>
        <option value="hi">हिन्दी</option>
      </select>
    </label>
  );
}

export function Header() {
  const { t } = useI18n();
  const { pathname, hash } = useLocation();
  const isHome = pathname === "/";
  return (
    <header className="app-header">
      <a href="/" className="app-brand" aria-current={isHome && !hash ? "page" : undefined}><span className="app-brand-mark">त</span><strong>{t("app.name")}</strong><small>INDEPENDENT PROTOTYPE</small></a>
      <nav aria-label="Primary"><a href="/#how" aria-current={isHome && hash === "#how" ? "location" : undefined}>HOW IT WORKS</a><a href="/#trust" aria-current={isHome && hash === "#trust" ? "location" : undefined}>SAFETY</a></nav>
      <LanguageSelector />
    </header>
  );
}

export function Stepper({ current }: { current: 0 | 1 | 2 | 3 | 4 | 5 }) {
  const { t } = useI18n();
  const steps = ["step.understand", "step.questions", "step.documents", "step.response", "step.review", "step.act"];
  return (
    <ol className="app-stepper" aria-label="Progress">
      {steps.map((key, i) => (
        <li key={key} className={i === current ? "is-current" : i < current ? "is-done" : ""} aria-current={i === current ? "step" : undefined}>
          <span>{String(i + 1).padStart(2, "0")}</span><strong>{t(key)}</strong>
        </li>
      ))}
    </ol>
  );
}

export function WorkflowRail({ current = 0 }: { current?: 0 | 1 | 2 | 3 | 4 | 5 }) {
  const { locale } = useI18n();
  const labels = locale === "hi"
    ? ["समझें", "सवाल", "दस्तावेज़", "उत्तर", "समीक्षा", "कार्रवाई"]
    : ["Understand", "Questions", "Documents", "Response", "Review", "Act"];
  const paths = ["/notices", "/notices", "/notices", "/notices", "/notices", "/notices"];
  return <aside className="workflow-rail" aria-label={locale === "hi" ? "आपकी प्रगति" : "Your progress"}>
    <p className="workflow-rail-kicker">{locale === "hi" ? "आपकी यात्रा" : "YOUR JOURNEY"}</p>
    <ol>{labels.map((label, index) => <li key={label} className={index === current ? "is-current" : index < current ? "is-done" : ""}>
      <Link to={paths[index]} aria-current={index === current ? "step" : undefined}><span>{index < current ? "✓" : String(index + 1).padStart(2, "0")}</span>{label}</Link>
    </li>)}</ol>
    <p className="workflow-next"><strong>{locale === "hi" ? "अगला कदम" : "NEXT"}</strong><span>{labels[Math.min(current + 1, labels.length - 1)]}</span></p>
  </aside>;
}

export function SavedGuidanceBadge({ show }: { show: boolean }) {
  const { t } = useI18n();
  if (!show) return null;
  return <span className="app-saved">■ {t("notice.savedGuidance")}</span>;
}

export function SourcePanel({ citation, onClose }: { citation: Citation | null; onClose: () => void }) {
  const { t } = useI18n();
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!citation) return;
    const previous = document.activeElement as HTMLElement | null;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    document.addEventListener("keydown", closeOnEscape);
    closeRef.current?.focus();
    return () => { document.removeEventListener("keydown", closeOnEscape); previous?.focus(); };
  }, [citation, onClose]);
  if (!citation) return null;
  return (
    <div className="source-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="source-dialog-title">
      <div className="source-panel" onClick={(e) => e.stopPropagation()}>
        <div className="source-head">
          <div>
            <p className="app-section-label">[ OFFICIAL SOURCE ]</p>
            <h3 id="source-dialog-title">{citation.title}</h3>
            <p className="source-section">{citation.source_name} · {citation.section}</p>
          </div>
          <button ref={closeRef} onClick={onClose} className="source-close">{t("notice.close")} ×</button>
        </div>
        <p className={`source-verification ${citation.verification === "verified" ? "is-verified" : ""}`}>
          ■ {citation.verification === "verified" ? t("notice.verification.verified") : t("notice.verification.pending")}
        </p>
        <blockquote className="source-excerpt">{citation.excerpt}</blockquote>
        <div className="source-footer">
          <a href={citation.official_url} target="_blank" rel="noopener noreferrer">{t("notice.viewSource")} ↗</a>
          <p>{citation.source_name} · accessed {citation.accessed_date}</p>
        </div>
      </div>
    </div>
  );
}

export function CitationChips({ citations }: { citations: Citation[] }) {
  const { t } = useI18n();
  const [open, setOpen] = useState<Citation | null>(null);
  return (
    <div>
      <p className="app-section-label">[ {t("notice.basedOn")} ]</p>
      <div className="citation-list">
        {citations.map((c, index) => (
          <button key={c.id} onClick={() => setOpen(c)}>
            <span>{String(index + 1).padStart(2, "0")}</span>{c.section || c.title}<b>↗</b>
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
}: {
  children: ReactNode;
  onClick?: () => void;
  href?: string;
  disabled?: boolean;
}) {
  const cls = "app-primary";
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
  return <div className="app-status"><span className={tone}>{text}</span>{label && <small>{label}</small>}</div>;
}
