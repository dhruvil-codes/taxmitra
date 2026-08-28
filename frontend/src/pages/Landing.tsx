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
    "May answer from broad knowledge",
    "No deterministic tax workflow",
    "No structured response path",
    "No official-source workflow by default",
  ],
  taxMitra: [
    "Notice-specific workflow",
    "Verified knowledge base and citations",
    "Deterministic rules and dynamic questions",
    "Document checklist and response preparation",
    "Refuses when uncertain · Human approval",
  ],
};

function Mark() {
  return <span className="tm-mark" aria-hidden="true">त</span>;
}

function ArrowLink({ children, onClick, light = false }: { children: React.ReactNode; onClick?: () => void; light?: boolean }) {
  return (
    <button className={`tm-button${light ? " tm-button-light" : ""}`} onClick={onClick}>
      <span>{children}</span><span aria-hidden="true">→</span>
    </button>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const { locale, setLocale } = useI18n();
  const openGuide = () => navigate("/guide");

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
          <button className={locale === "en" ? "is-active" : ""} onClick={() => setLocale("en")} aria-pressed={locale === "en"}>EN</button>
          <button className={locale === "hi" ? "is-active" : ""} onClick={() => setLocale("hi")} aria-pressed={locale === "hi"} lang="hi">हिन्दी</button>
        </div>
        <button className="tm-open" onClick={openGuide}>USE TAX MITRA <span>→</span></button>
      </header>

      <section className="tm-dark-hero" id="top">
        <div className="tm-hero-copy">
          <p className="tm-eyebrow tm-eyebrow-dark">◆ BUILT FOR INDIAN TAXPAYERS</p>
          <h1>Tax Mitra</h1>
          <p className="tm-hero-lede">Your tax notice, made understandable. Simple guidance for what happened, what you need, and what to do next.</p>
          <p className="tm-meta">TM / NOTICE / 2026 · INDEPENDENT PROTOTYPE · SYNTHETIC DATA</p>
        </div>
        <div className="tm-blocks" aria-hidden="true">
          {[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16].map((n) => <i key={n} />)}
        </div>
        <span className="tm-scroll">SCROLL FOR CLARITY ↓</span>
      </section>

      <div className="tm-principles" aria-label="Product principles">
        <span>→ AI EXPLAINS</span><span>→ RULES DECIDE</span><span>→ HUMANS APPROVE</span><span>→ NO AUTOMATIC SUBMISSIONS</span>
      </div>

      <main>
        <section className="tm-intro tm-wrap" id="india">
          <div>
            <p className="tm-eyebrow">[ TM / GUIDE / 01 ]</p>
            <h2>Understand your<br/><em>[ tax notice ]</em><br/>without the<br/>confusion.</h2>
          </div>
          <aside className="tm-intro-aside" aria-label="Start using Tax Mitra">
            <p className="tm-start-label"><Mark /> {locale === "hi" ? <span lang="hi">यहाँ से शुरू करें</span> : "START HERE"}</p>
            <div className="tm-intro-actions">
              <ArrowLink onClick={openGuide}>USE TAX MITRA</ArrowLink>
              <a href="/upload" className="tm-upload-action">
                <span>USE MY PDF NOTICE</span>
                <small lang={locale === "hi" ? "hi" : "en"}>{locale === "hi" ? "अपना नोटिस चुनें" : "Choose your notice PDF"}</small>
                <b aria-hidden="true">→</b>
              </a>
            </div>
            <a href="#how" className="tm-watch">See how it works <span aria-hidden="true">↓</span></a>
            <small className="tm-start-note">You stay in control. Nothing is submitted automatically.</small>
          </aside>
        </section>

        <section className="tm-promises tm-wrap" aria-label="Core promises">
          {promises.map(([number, title, copy]) => (
            <article key={number}>
              <p><b>{number}</b> {title}</p>
              <span>{copy}</span>
            </article>
          ))}
          <div className="tm-promise-rule">&gt; CLARITY → PREPARATION → CONFIDENT NEXT STEPS &lt;</div>
        </section>

        <section className="tm-process" id="how">
          <div className="tm-wrap tm-process-grid">
            <div>
              <p className="tm-eyebrow tm-eyebrow-dark">[ 02 / HOW IT WORKS ]</p>
              <h2>A simple path from<br/><em>[ notice ]</em> to next<br/>step.</h2>
            </div>
            <div className="tm-process-list">
              {steps.map((step, i) => (
                <details key={step} className="tm-process-item" open={i === 0}>
                  <summary>
                    <b>{String(i + 1).padStart(2, "0")}</b>
                    <span>{step}</span>
                    <i>→</i>
                  </summary>
                  <div className="tm-process-detail">
                    <p>This step helps you understand and prepare for the next action in your tax notice response journey.</p>
                  </div>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="tm-questions tm-wrap">
          <div>
            <p className="tm-eyebrow">[ PRODUCT PRINCIPLE ]</p>
            <h2>NO FORMS.<br/><em>NO UNNECESSARY<br/>QUESTIONS.</em></h2>
          </div>
          <div className="tm-questions-content">
            <p className="tm-questions-lede">Tax Mitra asks only what is necessary to safely guide the taxpayer.</p>
            <div className="tm-questions-list">
              <div className="tm-questions-item">
                <span className="tm-questions-icon">01</span>
                <div>
                  <b>CURRENT PROTOTYPE</b>
                  <p>Demo notices are pre-loaded for immediate exploration.</p>
                </div>
              </div>
              <div className="tm-questions-item">
                <span className="tm-questions-icon">02</span>
                <div>
                  <b>142(1) DEMO</b>
                  <p>Synthetic PDF extraction → taxpayer confirmation → guided preparation</p>
                </div>
              </div>
            </div>
            <small className="tm-questions-note">Your own PDF can be selected locally, but is not uploaded or extracted in this prototype.</small>
          </div>
        </section>

        <section className="tm-comparison">
          <div className="tm-wrap">
            <p className="tm-eyebrow">[ A FACTUAL COMPARISON ]</p>
            <h2>Why not just ask ChatGPT?</h2>
            <p className="tm-section-lede">Different tools are built for different jobs. Tax Mitra provides a bounded, notice-specific path.</p>
            <div className="tm-compare-grid">
              <article><h3>ChatGPT</h3>{comparison.chatgpt.map(x => <p key={x}>— {x}</p>)}</article>
              <article className="is-blue"><h3><Mark /> Tax Mitra</h3>{comparison.taxMitra.map(x => <p key={x}>→ {x}</p>)}</article>
            </div>
          </div>
        </section>

        <section className="tm-trust tm-wrap" id="trust">
          <div>
            <p className="tm-eyebrow">[ BUILT FOR TRUST ]</p>
            <h2>Clear help.<br/>Clear<br/>boundaries.</h2>
            <p>Tax Mitra explains and prepares. It never decides your liability, invents facts, or submits anything for you.</p>
          </div>
          <div className="tm-trust-grid">
            <article><i>□</i><h3>Private by design</h3><p>Your information is designed to remain under your control.</p></article>
            <article><i>文</i><h3>Easy to understand</h3><p>Plain language, with English and Hindi support.</p></article>
            <article><i>◉</i><h3>Built for everyday taxpayers</h3><p>Readable, mobile-friendly, and accessible.</p></article>
            <article><i>◇</i><h3>You approve</h3><p>Important actions remain in the taxpayer&apos;s hands.</p></article>
          </div>
        </section>

        <section className="tm-privacy">
          <div className="tm-wrap tm-privacy-grid">
            <p className="tm-eyebrow tm-eyebrow-dark">[ PRIVACY / V1 ]</p>
            <h2>Your information<br/>stays in your browser.</h2>
            <p>Tax Mitra is a tool, not a government service. The V1 architecture avoids persistent taxpayer storage.</p>
          </div>
        </section>

        <section className="tm-final tm-wrap">
          <p className="tm-eyebrow">[ READY WHEN YOU ARE ]</p>
          <h2>Understand your notice.<br/><em>Know what to do next.</em></h2>
          <ArrowLink onClick={openGuide}>USE TAX MITRA →</ArrowLink>
          <p>Independent civic prototype. Synthetic data. Not affiliated with the Income Tax Department. Tax Mitra does not submit anything.</p>
        </section>
      </main>

      <footer className="tm-footer tm-wrap">
        <a className="tm-brand" href="#top"><Mark /><strong>Tax Mitra</strong></a>
        <p>Independent civic prototype.</p>
        <nav><a href="#how">How it works</a><a href="#india">Built for India</a><a href="#trust">Trust</a><button onClick={openGuide}>Use Tax Mitra</button></nav>
        <div className="tm-footer-credit">
          <span>Built by</span>
          <a href="https://x.com/bydhruvil" target="_blank" rel="noopener noreferrer">@bydhruvil</a>
        </div>
      </footer>
    </div>
  );
}
