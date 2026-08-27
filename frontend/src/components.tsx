import { ReactNode, useState } from "react";
import { useI18n } from "./i18n";
import { Citation, Locale } from "./lib";

export function DisclaimerBanner() {
  const { t } = useI18n();
  return <div className="app-disclaimer">[ PUBLIC BETA ] &nbsp; {t("banner")}</div>;
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
  return (
    <header className="app-header">
      <a href="/" className="app-brand"><span className="app-brand-mark">त</span><strong>{t("app.name")}</strong><small>INDEPENDENT PROTOTYPE</small></a>
      <nav aria-label="Primary"><a href="/#how">HOW IT WORKS</a><a href="/#trust">SAFETY</a></nav>
      <LanguageSelector />
    </header>
  );
}

export function Stepper({ current }: { current: 0 | 1 | 2 | 3 }) {
  const { t } = useI18n();
  const steps = ["step.understand", "step.answer", "step.prepare", "step.act"];
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

export function SavedGuidanceBadge({ show }: { show: boolean }) {
  const { t } = useI18n();
  if (!show) return null;
  return <span className="app-saved">■ {t("notice.savedGuidance")}</span>;
}

export function SourcePanel({ citation, onClose }: { citation: Citation | null; onClose: () => void }) {
  const { t } = useI18n();
  if (!citation) return null;
  return (
    <div className="source-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label={citation.title}>
      <div className="source-panel" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-stone-500">{citation.source_name}</p>
            <h3 className="font-bold text-ink leading-snug">{citation.title}</h3>
            <p className="text-sm text-saffron font-medium">{citation.section}</p>
          </div>
          <button
            onClick={onClose}
            className="text-stone-500 hover:text-ink text-sm border border-stone-300 rounded-lg px-2 py-1"
          >
            {t("notice.close")}
          </button>
        </div>
        <div
          className={`mt-3 text-xs rounded-lg px-2.5 py-1.5 inline-block ${
            citation.verification === "verified"
              ? "bg-india-green-soft text-india-green"
              : "bg-amber-50 text-amber-800"
          }`}
        >
          {citation.verification === "verified"
            ? t("notice.verification.verified")
            : t("notice.verification.pending")}
        </div>
        <blockquote className="mt-3 text-sm text-stone-700 leading-relaxed border-l-4 border-saffron/40 pl-3 whitespace-pre-line">
          {citation.excerpt}
        </blockquote>
        <div className="mt-4 flex flex-col gap-2">
          <a
            href={citation.official_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-semibold text-india-green underline"
          >
            {t("notice.viewSource")}
          </a>
          <p className="text-[11px] text-stone-400">
            {citation.source_name} · accessed {citation.accessed_date}
          </p>
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
      <p className="text-xs font-semibold text-stone-500 uppercase tracking-wide mb-2">
        {t("notice.basedOn")}
      </p>
      <div className="flex flex-wrap gap-2">
        {citations.map((c) => (
          <button
            key={c.id}
            onClick={() => setOpen(c)}
            className="text-xs font-medium bg-white border border-stone-300 hover:border-saffron rounded-full px-3 py-1.5 text-left"
          >
            {c.section || c.title}
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
}: {
  children: ReactNode;
  onClick?: () => void;
  href?: string;
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
    <button onClick={onClick} className={cls}>
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
