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
          {locale === "hi" ? "सैंपल नोटिस आज़माएं" : "Try a sample notice"} <span>→</span>
        </button>
      </header>

      {/* 5-SECOND CLARITY HERO */}
      <section className="tm-dark-hero tm-hero-reworked" id="top">
        <div className="tm-hero-copy">
          <p className="tm-eyebrow tm-eyebrow-dark">
            {locale === "hi" ? "भारतीय करदाताओं के लिए मार्गदर्शक" : "BUILT FOR INDIAN TAXPAYERS"}
          </p>
          <h1 className="tm-hero-title">
            {locale === "hi" ? (
              <>
                आपका टैक्स नोटिस,<br />
                अब समझने में आसान।
              </>
            ) : (
              <>
                YOUR TAX NOTICE,<br />
                MADE UNDERSTANDABLE.
              </>
            )}
          </h1>
          <p className="tm-hero-lede">
            {locale === "hi"
              ? "समझें कि आपके नोटिस में क्या मांगा गया है, कौन-सी जानकारी चाहिए और अगला क्या करना है।"
              : "Understand what your notice asks, what information you may need, and what to do next."}
          </p>
          <p className="tm-hero-scope">{t("landing.heroScope")}</p>

          <div className="tm-hero-actions">
            <button className="tm-button tm-button-blue" onClick={() => navigate("/upload")}>
              <span>{locale === "hi" ? "अपना नोटिस अपलोड करें" : "Upload your notice"}</span>
              <span aria-hidden="true">→</span>
            </button>
            <button className="tm-button tm-button-outline" onClick={() => navigate("/login")}>
              <span>{locale === "hi" ? "सैंपल नोटिस आज़माएं" : "Try a sample notice"}</span>
              <span aria-hidden="true">→</span>
            </button>
          </div>

          {/* VISUAL STORY: NOTICE → UNDERSTAND → PREPARE → REVIEW → ACT */}
          <div className="tm-hero-flow" aria-label="Visual process flow">
            <span className="tm-hero-flow-item">NOTICE</span>
            <span className="tm-hero-flow-arrow" aria-hidden="true">→</span>
            <span className="tm-hero-flow-item is-active">UNDERSTAND</span>
            <span className="tm-hero-flow-arrow" aria-hidden="true">→</span>
            <span className="tm-hero-flow-item">PREPARE</span>
            <span className="tm-hero-flow-arrow" aria-hidden="true">→</span>
            <span className="tm-hero-flow-item">REVIEW</span>
            <span className="tm-hero-flow-arrow" aria-hidden="true">→</span>
            <span className="tm-hero-flow-item">ACT</span>
          </div>

          <p className="tm-hero-boundary">
            {locale === "hi"
              ? "स्वतंत्र प्रोटोटाइप · सिंथेटिक डेटा · सरकार को कोई स्वचालित जमा नहीं"
              : "Independent prototype · Synthetic demo data · No automatic government submission"}
          </p>
        </div>
      </section>

      <main>
        <section className="tm-intro tm-wrap" id="india">
          <div>
            <p className="tm-eyebrow">
              {locale === "hi" ? "[ TM / गाइड / 01 ]" : "[ TM / GUIDE / 01 ]"}
            </p>
            {locale === "hi" ? (
              <h2>
                अपनी टैक्स नोटिस<br />
                <em>[ बिना किसी भ्रम ]</em><br />
                के समझें।
              </h2>
            ) : (
              <h2>
                Understand your<br />
                <em>[&nbsp;tax notice&nbsp;]</em><br />
                without the<br />
                confusion.
              </h2>
            )}
          </div>
          <aside className="tm-intro-aside" aria-label="Start using Tax Mitra">
            <p className="tm-start-label">
              <Mark /> {locale === "hi" ? <span lang="hi">यहाँ से शुरू करें</span> : "START HERE"}
            </p>
            <div className="tm-intro-actions">
              <ArrowLink onClick={() => navigate("/login")}>
                {locale === "hi" ? "सैंपल नोटिस आज़माएं" : "Try a sample notice"}
              </ArrowLink>
              <a href="/upload" className="tm-upload-action">
                <span>{locale === "hi" ? "अपना नोटिस अपलोड करें" : "Upload your notice"}</span>
                <small lang={locale === "hi" ? "hi" : "en"}>
                  {locale === "hi" ? "PDF फ़ाइल चुनें" : "Choose your notice PDF"}
                </small>
                <b aria-hidden="true">→</b>
              </a>
            </div>
            <a href="#how" className="tm-watch">
              {locale === "hi" ? "देखें यह कैसे काम करता है" : "See how it works"} <span aria-hidden="true">↓</span>
            </a>
            <small className="tm-start-note">
              {locale === "hi"
                ? "आप पूर्ण नियंत्रण में रहते हैं। कुछ भी स्वचालित रूप से जमा नहीं होता है।"
                : "You stay in control. Nothing is submitted automatically."}
            </small>
          </aside>
        </section>

        <section className="tm-promises tm-wrap" aria-label="Core promises">
          {promises.map(([number, title, copy]) => (
            <article key={number}>
              <p>
                <b>{number}</b> {t(`landing.promise${number}`)}
              </p>
              <span>{t(`landing.promise${number}Desc`)}</span>
            </article>
          ))}
          <div className="tm-promise-rule">{t("landing.promiseRule")}</div>
        </section>

        <section className="tm-process" id="how">
          <div className="tm-wrap tm-process-grid">
            <div>
              <p className="tm-eyebrow tm-eyebrow-dark">HOW IT WORKS</p>
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
            <p className="tm-eyebrow">PRODUCT PRINCIPLE</p>
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
            <p className="tm-eyebrow">FACTUAL COMPARISON</p>
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
            <p className="tm-eyebrow">BUILT FOR TRUST</p>
            <h2>{t("landing.trustTitle")}</h2>
            <p>{t("landing.trustSub")}</p>
          </div>
          <div className="tm-trust-grid">
            <article>
              <i>□</i>
              <h3>{t("landing.trust01")}</h3>
              <p>{t("landing.trust01Desc")}</p>
            </article>
            <article>
              <i>文</i>
              <h3>{t("landing.trust02")}</h3>
              <p>{t("landing.trust02Desc")}</p>
            </article>
            <article>
              <i>◉</i>
              <h3>{t("landing.trust03")}</h3>
              <p>{t("landing.trust03Desc")}</p>
            </article>
            <article>
              <i>◇</i>
              <h3>{t("landing.trust04")}</h3>
              <p>{t("landing.trust04Desc")}</p>
            </article>
          </div>
        </section>

        <section className="tm-privacy">
          <div className="tm-wrap tm-privacy-grid">
            <p className="tm-eyebrow tm-eyebrow-dark">PRIVACY FIRST</p>
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
        <a className="tm-brand" href="#top">
          <Mark />
          <strong>Tax Mitra</strong>
        </a>
        <p>{t("landing.footer")}</p>
        <nav>
          <a href="#how">{t("landing.footerLink1")}</a>
          <a href="#india">{t("landing.footerLink2")}</a>
          <a href="#trust">{t("landing.footerLink3")}</a>
          <button onClick={() => navigate("/login")}>
            {locale === "hi" ? "सैंपल नोटिस आज़माएं" : "Try a sample notice"}
          </button>
        </nav>
        <div className="tm-footer-credit">
          <span>{t("landing.builtBy")}</span>
          <a href="https://x.com/bydhruvil" target="_blank" rel="noopener noreferrer">
            @bydhruvil
          </a>
        </div>
        <p className="tm-footer-disclaimer">{t("landing.disclaimer")}</p>
      </footer>
    </div>
  );
}
