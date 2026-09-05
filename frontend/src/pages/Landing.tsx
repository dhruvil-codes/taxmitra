import { useNavigate } from "react-router-dom";
import { useI18n } from "../i18n";

const promises = [
  ["01", "PLAIN LANGUAGE", "Simple explanations without legal jargon."],
  ["02", "GUIDED STEPS", "A focused path from notice to next action."],
  ["03", "DOCUMENT HELP", "Prepare only the documents your notice needs."],
  ["04", "HUMAN CONTROL", "You approve every important action."],
];

const steps = [
  "Understand your notice",
  "See what the department is asking",
  "Answer only what is necessary",
  "Prepare your documents and response",
  "Review everything",
  "Continue to the official portal",
];

const comparison = {
  chatgpt: [
    "General-purpose",
    "May answer from broad training data",
    "No deterministic tax workflow",
    "No structured response path",
    "No official-source citations by default",
  ],
  taxMitra: [
    "Notice-specific guided workflow",
    "Verified knowledge base & CBDT citations",
    "Deterministic rules & dynamic questions",
    "Evidence checklist & response drafting",
    "Refuses when uncertain · Human approval gate",
  ],
};

function Mark() {
  return <span className="tm-mark" aria-hidden="true">त</span>;
}

function ArrowLink({
  children,
  onClick,
  light = false,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  light?: boolean;
}) {
  return (
    <button className={`tm-button${light ? " tm-button-light" : ""}`} onClick={onClick}>
      <span>{children}</span>
      <span aria-hidden="true">→</span>
    </button>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const { locale, setLocale, t } = useI18n();

  return (
    <div className="tm-site">
      <header className="tm-nav">
        <a className="tm-brand" href="#top" aria-label="Tax Mitra home">
          <Mark />
          <strong>Tax Mitra</strong>
          <span>INDEPENDENT PROTOTYPE</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#how">HOW IT WORKS</a>
          <a href="#india">BUILT FOR INDIA</a>
          <a href="#trust">TRUST</a>
        </nav>
        <div className="tm-languages" aria-label="Languages">
          <button
            className={locale === "en" ? "is-active" : ""}
            onClick={() => setLocale("en")}
            aria-pressed={locale === "en"}
          >
            EN
          </button>
          <button
            className={locale === "hi" ? "is-active" : ""}
            onClick={() => setLocale("hi")}
            aria-pressed={locale === "hi"}
            lang="hi"
          >
            हिन्दी
          </button>
        </div>
        <button className="tm-open" onClick={() => navigate("/login")}>
          <span className="tm-open-text-full">{locale === "hi" ? "सैंपल नोटिस आज़माएं" : "Try a sample notice"}</span>
          <span className="tm-open-text-compact">{locale === "hi" ? "सैंपल" : "Sample"}</span>
          <span aria-hidden="true">→</span>
        </button>
      </header>

      <section className="tm-dark-hero tm-hero-reworked" id="top" aria-labelledby="hero-title">
        <div className="tm-hero-copy">
          <p className="tm-eyebrow tm-eyebrow-dark">
            <span className="tm-dot" aria-hidden="true" />
            {locale === "hi" ? "भारतीय करदाताओं के लिए मार्गदर्शक" : "Built for Indian taxpayers"}
          </p>
          <h1 className="tm-hero-title" id="hero-title">
            {locale === "hi" ? (
              <>आपका टैक्स नोटिस,<br />अब समझना आसान।</>
            ) : (
              <>Your tax notice,<br />made understandable.</>
            )}
          </h1>
          <p className="tm-hero-lede">
            {locale === "hi"
              ? "समझें कि आपके नोटिस में क्या मांगा गया है, कौन-सी जानकारी चाहिए और अगला कदम क्या है।"
              : "Understand what your notice asks, what information you may need, and what to do next."}
          </p>
          <p className="tm-hero-scope">{t("landing.heroScope")}</p>

          <div className="tm-hero-actions">
            <button className="tm-button tm-button-blue" onClick={() => navigate("/upload")}>
              <span>{locale === "hi" ? "अपना नोटिस अपलोड करें" : "Upload your notice"}</span>
              <span aria-hidden="true">↗</span>
            </button>
            <button className="tm-button tm-button-outline" onClick={() => navigate("/login")}>
              <span>{locale === "hi" ? "सैंपल नोटिस आज़माएं" : "Try a sample notice"}</span>
              <span aria-hidden="true">→</span>
            </button>
          </div>

          <ol className="tm-hero-flow" aria-label={locale === "hi" ? "नोटिस से कार्रवाई तक" : "From notice to action"}>
            {(locale === "hi"
              ? ["नोटिस", "समझें", "तैयार करें", "समीक्षा", "कार्रवाई"]
              : ["Notice", "Understand", "Prepare", "Review", "Act"]
            ).map((label, index) => (
              <li className={index === 1 ? "is-active" : ""} key={label}>
                <span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
                {label}
              </li>
            ))}
          </ol>

          <p className="tm-hero-boundary">
            {locale === "hi"
              ? "स्वतंत्र प्रोटोटाइप · सिंथेटिक डेटा · सरकार को कोई स्वचालित जमा नहीं"
              : "Independent prototype · Synthetic demo data · No automatic government submission"}
          </p>
        </div>

        <aside className="tm-notice-preview" aria-label={locale === "hi" ? "नोटिस विश्लेषण का उदाहरण" : "Example notice analysis"}>
          <div className="tm-notice-preview-bar">
            <span>{locale === "hi" ? "नोटिस विश्लेषण" : "Notice analysis"}</span>
            <b>{locale === "hi" ? "तैयार" : "Ready"}</b>
          </div>
          <div className="tm-notice-sheet">
            <div className="tm-notice-sheet-head">
              <Mark />
              <div>
                <span>Income Tax Department</span>
                <strong>Section 142(1)</strong>
              </div>
              <small>AY 2024–25</small>
            </div>
            <div className="tm-notice-lines" aria-hidden="true">
              <i /><i /><i /><i />
            </div>
            <div className="tm-notice-finding">
              <span>{locale === "hi" ? "आपसे क्या मांगा गया है" : "What they are asking for"}</span>
              <strong>{locale === "hi" ? "आय और कटौती के सहायक दस्तावेज़" : "Supporting documents for income and deductions"}</strong>
            </div>
            <ul className="tm-notice-checklist">
              <li><span aria-hidden="true" />{locale === "hi" ? "समय सीमा पहचान ली गई" : "Deadline identified"}</li>
              <li><span aria-hidden="true" />{locale === "hi" ? "ज़रूरी दस्तावेज़ सूचीबद्ध" : "Required documents listed"}</li>
              <li><span aria-hidden="true" />{locale === "hi" ? "अगले कदम स्पष्ट किए गए" : "Next steps explained"}</li>
            </ul>
          </div>
          <p>{locale === "hi" ? "आपकी समीक्षा के बिना कुछ भी आगे नहीं बढ़ता।" : "Nothing moves forward without your review."}</p>
        </aside>
      </section>

      <main>
        <section className="tm-intro tm-wrap" id="india">
          <div className="tm-intro-heading">
            <p className="tm-eyebrow">{locale === "hi" ? "स्पष्टता, शुरू से अंत तक" : "Clarity, from start to finish"}</p>
            <h2>
              {locale === "hi" ? "एक कठिन नोटिस को स्पष्ट अगले कदमों में बदलें।" : "Turn a difficult notice into clear next steps."}
            </h2>
          </div>
          <p className="tm-intro-lede">
            {locale === "hi"
              ? "Tax Mitra विभाग की भाषा को समझने योग्य बनाता है, ज़रूरी रिकॉर्ड पहचानता है और आपकी समीक्षा के लिए एक सीमित, सुरक्षित रास्ता तैयार करता है।"
              : "Tax Mitra translates departmental language, identifies the records that matter, and gives you a bounded path to review before you act."}
          </p>
          <div className="tm-promises" aria-label={locale === "hi" ? "मुख्य विशेषताएँ" : "Core features"}>
            {promises.map(([number]) => (
              <article key={number}>
                <span>{number}</span>
                <div>
                  <h3>{t(`landing.promise${number}`)}</h3>
                  <p>{t(`landing.promise${number}Desc`)}</p>
                </div>
              </article>
            ))}
          </div>
          <p className="tm-intro-principle">
            {locale === "hi" ? "AI समझाता है। नियम तय करते हैं। आप मंज़ूरी देते हैं।" : "AI explains. Rules decide. You approve."}
          </p>
        </section>

        <section className="tm-process" id="how">
          <div className="tm-wrap tm-process-grid">
            <div>
              <p className="tm-eyebrow tm-eyebrow-dark">
                {locale === "hi" ? "यह कैसे काम करता है" : "How it works"}
              </p>
              <h2 dangerouslySetInnerHTML={{ __html: t("landing.howTitle") }} />
            </div>
            <div className="tm-process-list">
              {steps.map((step, i) => (
                <details key={step} className="tm-process-item" open={i === 0}>
                  <summary>
                    <b>{String(i + 1).padStart(2, "0")}</b>
                    <span>{t(`landing.step${i + 1}`)}</span>
                    <i>→</i>
                  </summary>
                  <div className="tm-process-detail">
                    <p>{t(`landing.step${i + 1}Detail`)}</p>
                  </div>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="tm-questions tm-wrap">
          <div>
            <p className="tm-eyebrow">
              {locale === "hi" ? "उत्पाद सिद्धांत" : "Product principle"}
            </p>
            <h2>{t("landing.principleTitle")}</h2>
          </div>
          <div className="tm-questions-content">
            <p className="tm-questions-lede">{t("landing.principleLede")}</p>
            <div className="tm-questions-list">
              <div className="tm-questions-item">
                <span className="tm-questions-icon">01</span>
                <div>
                  <b>{t("landing.principle01")}</b>
                  <p>{t("landing.principle01Desc")}</p>
                </div>
              </div>
              <div className="tm-questions-item">
                <span className="tm-questions-icon">02</span>
                <div>
                  <b>{t("landing.principle02")}</b>
                  <p>{t("landing.principle02Desc")}</p>
                </div>
              </div>
            </div>
            <small className="tm-questions-note">{t("landing.principleNote")}</small>
          </div>
        </section>

        <section className="tm-comparison">
          <div className="tm-wrap">
            <p className="tm-eyebrow">
              {locale === "hi" ? "तथ्यात्मक तुलना" : "Factual comparison"}
            </p>
            <h2>{t("landing.comparisonTitle")}</h2>
            <p className="tm-section-lede">{t("landing.comparisonSub")}</p>
            <div className="tm-compare-grid">
              <article>
                <h3>ChatGPT</h3>
                {comparison.chatgpt.map((x) => (
                  <p key={x}>— {x}</p>
                ))}
              </article>
              <article className="is-blue">
                <h3><Mark /> Tax Mitra</h3>
                {comparison.taxMitra.map((x) => (
                  <p key={x}>→ {x}</p>
                ))}
              </article>
            </div>
          </div>
        </section>

        <section className="tm-trust tm-wrap" id="trust">
          <div>
            <p className="tm-eyebrow">
              {locale === "hi" ? "विश्वास के लिए निर्मित" : "Built for trust"}
            </p>
            <h2>{t("landing.trustTitle")}</h2>
            <p>{t("landing.trustSub")}</p>
          </div>
          <div className="tm-trust-grid">
            <article>
              <i>01</i>
              <h3>{t("landing.trust01")}</h3>
              <p>{t("landing.trust01Desc")}</p>
            </article>
            <article>
              <i>02</i>
              <h3>{t("landing.trust02")}</h3>
              <p>{t("landing.trust02Desc")}</p>
            </article>
            <article>
              <i>03</i>
              <h3>{t("landing.trust03")}</h3>
              <p>{t("landing.trust03Desc")}</p>
            </article>
            <article>
              <i>04</i>
              <h3>{t("landing.trust04")}</h3>
              <p>{t("landing.trust04Desc")}</p>
            </article>
          </div>
        </section>

        <section className="tm-privacy">
          <div className="tm-wrap tm-privacy-grid">
            <p className="tm-eyebrow tm-eyebrow-dark">
              {locale === "hi" ? "गोपनीयता" : "Privacy"}
            </p>
            <h2>{t("landing.privacyTitle")}</h2>
            <p>{t("landing.privacySub")}</p>
          </div>
        </section>

        <section className="tm-final tm-wrap">
          <p className="tm-eyebrow">{t("landing.ready")}</p>
          <h2>{t("landing.finalTitle")}</h2>
          <ArrowLink onClick={() => navigate("/login")}>
            {locale === "hi" ? "सैंपल नोटिस आज़माएं" : "Try a sample notice"}
          </ArrowLink>
          <p>{t("landing.finalSub")}</p>
        </section>
      </main>

      <footer className="tm-footer tm-wrap">
        <div className="tm-footer-primary">
          <a className="tm-brand" href="#top">
            <Mark />
            <strong>Tax Mitra</strong>
          </a>
          <nav aria-label={locale === "hi" ? "फुटर नेविगेशन" : "Footer navigation"}>
            <a href="#how">{t("landing.footerLink1")}</a>
            <a href="#trust">{t("landing.footerLink3")}</a>
            <a href="/upload">{locale === "hi" ? "नोटिस अपलोड करें" : "Upload notice"}</a>
          </nav>
        </div>
        <div className="tm-footer-meta">
          <p>{t("landing.disclaimer")}</p>
          <p className="tm-footer-credit">
            {t("landing.builtBy")} <a href="https://x.com/bydhruvil" target="_blank" rel="noopener noreferrer">@bydhruvil</a>
          </p>
        </div>
      </footer>
    </div>
  );
}
