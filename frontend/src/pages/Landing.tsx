import { useNavigate } from "react-router-dom";

const promises = [
  ["01", "PLAIN LANGUAGE", "Explain technical tax language in simple words."],
  ["02", "INDIAN CONTEXT", "Designed around the way Indian taxpayers actually encounter tax notices."],
  ["03", "MOBILE FIRST", "Readable and usable on phones and low-bandwidth connections."],
  ["04", "HUMAN CONTROL", "Tax Mitra prepares guidance. You approve every important action."],
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
        <div className="tm-languages" aria-label="Languages"><b>EN</b><span>हिन्दी</span></div>
        <button className="tm-open" onClick={openGuide}>OPEN GUIDE <span>→</span></button>
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
          <aside className="tm-intro-aside">
            <p className="tm-proof"><span className="tm-proof-faces">TM</span> Trusted civic guidance <b>★ 4.9 / 5</b></p>
            <p>Tax Mitra explains what your notice means, shows what to prepare, and helps you draft a response in plain language.</p>
            <div className="tm-intro-actions">
              <ArrowLink onClick={openGuide}>OPEN GUIDE</ArrowLink>
              <a href="#how" className="tm-watch"><span>▷</span> HOW IT WORKS</a>
            </div>
            <a href="#language">⌁ Understand in your language</a>
            <p className="tm-language-copy" id="language">English / हिन्दी</p>
            <small>Independent prototype · Synthetic data · Not affiliated with the Income Tax Department · No automatic submissions</small>
          </aside>
        </section>

        <section className="tm-promises tm-wrap" aria-label="Core promises">
          {promises.map(([number, title, copy]) => (
            <article key={number}>
              <p><b>{number}</b> {title}</p>
              <span>{copy}</span>
            </article>
          ))}
          <div className="tm-promise-rule"><span>···</span> &gt; ADD AN <b>INTELLIGENCE LAYER</b> FOR YOUR TAX NOTICE &lt; <span>···</span></div>
        </section>

        <section className="tm-value tm-wrap" aria-labelledby="value-heading">
          <div className="tm-value-head">
            <div>
              <p className="tm-eyebrow">[ IN.01 / 11 ] &nbsp; — &nbsp; KEY VALUE</p>
              <h2 id="value-heading">Less manual work.<br/>More confident action.</h2>
            </div>
            <button className="tm-mini-button" onClick={openGuide}>■ &nbsp; OPEN GUIDE</button>
          </div>
          <div className="tm-value-grid">
            <article>
              <span className="tm-card-number">// 001</span>
              <div className="tm-diagram tm-diagram-one" aria-hidden="true"><i/><i/><i/></div>
              <h3>Plain-language clarity</h3>
              <p>Turn dense notice language into a clear summary of what happened and why it matters.</p>
            </article>
            <article className="is-featured">
              <span className="tm-card-number">// 002</span>
              <div className="tm-diagram tm-diagram-two" aria-hidden="true"><i/><i/><i/><i/></div>
              <h3>Adaptive guidance</h3>
              <p>Follow a focused path that adapts to the notice, your answers, and the documents you have.</p>
            </article>
            <article>
              <span className="tm-card-number">// 003</span>
              <div className="tm-diagram tm-diagram-three" aria-hidden="true"><i/><i/><i/></div>
              <h3>Human-controlled results</h3>
              <p>Prepare your next step with clear boundaries. Nothing is submitted without your approval.</p>
            </article>
          </div>
        </section>

        <section className="tm-process" id="how">
          <div className="tm-wrap tm-process-grid">
            <div>
              <p className="tm-eyebrow tm-eyebrow-dark">[ 02 / HOW IT WORKS ]</p>
              <h2>A simple path from<br/><em>[ notice ]</em> to next<br/>step.</h2>
            </div>
            <ol>
              {steps.map((step, i) => <li key={step}><b>{String(i + 1).padStart(2, "0")}</b><span>{step}</span><i>→</i></li>)}
            </ol>
          </div>
        </section>

        <section className="tm-questions tm-wrap">
          <div>
            <p className="tm-eyebrow">[ PRODUCT PRINCIPLE ]</p>
            <h2>NO FORMS.<br/><em>NO UNNECESSARY<br/>QUESTIONS.</em></h2>
          </div>
          <div className="tm-questions-copy">
            <p>Tax Mitra asks only what is necessary to safely guide the taxpayer.</p>
            <div><b>CURRENT PROTOTYPE</b><span>Demo notices are pre-loaded.</span></div>
            <div><b>FUTURE DIRECTION</b><span>Upload notice PDF → extract requests → taxpayer confirms → guided preparation</span></div>
            <small>PDF extraction is a future direction and is not implemented in this prototype.</small>
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
          <ArrowLink onClick={openGuide}>OPEN GUIDE</ArrowLink>
          <p>Independent civic prototype. Synthetic data. Not affiliated with the Income Tax Department. Tax Mitra does not submit anything.</p>
        </section>
      </main>

      <footer className="tm-footer tm-wrap">
        <a className="tm-brand" href="#top"><Mark /><strong>Tax Mitra</strong></a>
        <p>Independent civic prototype.</p>
        <nav><a href="#how">How it works</a><a href="#india">Built for India</a><a href="#trust">Trust</a><button onClick={openGuide}>Open Guide</button></nav>
      </footer>
    </div>
  );
}
