import { ReactNode, useState } from "react";
import { useI18n } from "./i18n";
import { Citation, Locale } from "./lib";

export function DisclaimerBanner() {
  const { t } = useI18n();
  return (
    <div className="bg-amber-100 text-amber-900 text-[11px] sm:text-xs text-center px-3 py-1.5 leading-snug">
      {t("banner")}
    </div>
  );
}

export function LanguageSelector() {
  const { locale, setLocale, t } = useI18n();
  return (
    <label className="flex items-center gap-1.5 text-sm">
      <span className="sr-only">{t("lang.label")}</span>
      <select
        aria-label={t("lang.label")}
        value={locale}
        onChange={(e) => setLocale(e.target.value as Locale)}
        className="border border-stone-300 rounded-lg px-2 py-1 bg-white text-ink font-medium"
      >
        <option value="en">English</option>
        <option value="hi">हिंदी</option>
      </select>
    </label>
  );
}

export function Header() {
  const { t } = useI18n();
  return (
    <header className="flex items-center justify-between gap-3 px-4 py-3 bg-white border-b border-stone-200">
      <a href="/" className="flex items-baseline gap-2">
        <span className="font-bold text-lg text-saffron">{t("app.name")}</span>
        <span className="hidden sm:inline text-xs text-stone-500">{t("app.tagline")}</span>
      </a>
      <LanguageSelector />
    </header>
  );
}

export function Stepper({ current }: { current: 0 | 1 | 2 | 3 }) {
  const { t } = useI18n();
  const steps = ["step.understand", "step.answer", "step.prepare", "step.act"];
  return (
    <ol className="flex items-center w-full max-w-xl mx-auto mb-6" aria-label="Progress">
      {steps.map((key, i) => (
        <li key={key} className="flex-1 flex items-center">
          <div className="flex flex-col items-center gap-1">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 ${
                i < current
                  ? "bg-india-green text-white border-india-green"
                  : i === current
                    ? "bg-white text-saffron border-saffron"
                    : "bg-white text-stone-400 border-stone-300"
              }`}
              aria-current={i === current ? "step" : undefined}
            >
              {i < current ? "✓" : i + 1}
            </div>
            <span
              className={`text-[10px] sm:text-xs ${i === current ? "text-saffron font-semibold" : "text-stone-500"}`}
            >
              {t(key)}
            </span>
          </div>
          {i < steps.length - 1 && <div className="flex-1 h-0.5 bg-stone-300 mx-1 -mt-4" />}
        </li>
      ))}
    </ol>
  );
}

export function SavedGuidanceBadge({ show }: { show: boolean }) {
  const { t } = useI18n();
  if (!show) return null;
  return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-india-green bg-india-green-soft border border-green-200 rounded-full px-2.5 py-1">
      {t("notice.savedGuidance")}
    </span>
  );
}

export function SourcePanel({ citation, onClose }: { citation: Citation | null; onClose: () => void }) {
  const { t } = useI18n();
  if (!citation) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={citation.title}
    >
      <div
        className="bg-white rounded-t-2xl sm:rounded-2xl max-w-lg w-full p-5 max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
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
  return (
    <div className={`bg-white border border-stone-200 rounded-2xl p-5 shadow-sm ${className}`}>
      {children}
    </div>
  );
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
  const cls =
    "inline-flex items-center justify-center gap-2 bg-saffron text-white font-semibold rounded-xl px-5 py-3 hover:bg-saffron/90 transition";
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
  const tone =
    status === "expired"
      ? "bg-red-50 text-red-700 border-red-200"
      : status === "due_soon"
        ? "bg-amber-50 text-amber-800 border-amber-200"
        : "bg-india-green-soft text-india-green border-green-200";
  const text =
    status === "expired"
      ? t("dash.overdue")
      : status === "due_soon"
        ? t("dash.dueSoon")
        : t("dash.actionRequired");
  return (
    <div className="flex flex-wrap gap-2">
      <span className={`text-xs font-semibold border rounded-full px-2.5 py-1 ${tone}`}>{text}</span>
      {label && <span className="text-xs font-medium text-stone-600 self-center">{label}</span>}
    </div>
  );
}
