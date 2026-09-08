import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useI18n } from "../i18n";

interface FlowStepData {
  stepNum: string;
  badge: { en: string; hi: string };
  badgeColor: string;
  barTitle: { en: string; hi: string };
  headTitle: { en: string; hi: string };
  headSubtitle: { en: string; hi: string };
  headMeta: { en: string; hi: string };
  accentColor: string;
  findingLabel: { en: string; hi: string };
  findingValue: { en: string; hi: string };
  checklist: { en: string[]; hi: string[] };
  footerText: { en: string; hi: string };
  visualKind: "scanner" | "standard" | "evidence" | "citations" | "portal";
}

const heroSteps: FlowStepData[] = [
  {
    stepNum: "01",
    badge: { en: "Scan", hi: "जांच" },
    badgeColor: "#0ea5e9",
    barTitle: { en: "01 Upload · Instant Read", hi: "01 अपलोड · तुरंत जांच" },
    headTitle: { en: "Income Tax Notice", hi: "आयकर नोटिस" },
    headSubtitle: { en: "Identify Notice Type", hi: "नोटिस प्रकार पहचानें" },
    headMeta: { en: "Verified Notice", hi: "प्रमाणित नोटिस" },
    accentColor: "#0ea5e9",
    findingLabel: { en: "What We Found", hi: "क्या सामने आया" },
    findingValue: {
      en: "Notice type identified: supported workflow or safe stop boundary",
      hi: "नोटिस प्रकार पहचाना गया: समर्थित कार्यप्रवाह या सुरक्षित सीमा",
    },
    checklist: {
      en: [
        "Due date found if applicable",
        "Notice authenticity and tax year verified",
        "Workflow capability determined",
      ],
      hi: [
        "यदि लागू हो तो अंतिम तारीख पाई गई",
        "नोटिस की प्रामाणिकता व वर्ष सत्यापित",
        "कार्यप्रवाह क्षमता निर्धारित",
      ],
    },
    footerText: {
      en: "Your notice stays private and safe on your device.",
      hi: "आपका नोटिस पूरी तरह सुरक्षित व निजी रहता है।",
    },
    visualKind: "scanner",
  },
  {
    stepNum: "02",
    badge: { en: "Summary", hi: "सारांश" },
    badgeColor: "#1b5cff",
    barTitle: { en: "02 Understand · Plain Words", hi: "02 समझें · सीधी भाषा" },
    headTitle: { en: "Plain-Language Summary", hi: "सीधे शब्दों में समझें" },
    headSubtitle: { en: "Why You Received This", hi: "यह नोटिस क्यों आया?" },
    headMeta: { en: "Workflow Guidance", hi: "कार्यप्रवाह मार्गदर्शन" },
    accentColor: "var(--tm-blue)",
    findingLabel: { en: "In Simple Words", hi: "सरल शब्दों में" },
    findingValue: {
      en: "Clear explanation of what the department is asking and your options",
      hi: "विभाग क्या मांग रहा है और आपके विकल्प क्या हैं, इसका स्पष्ट स्पष्टीकरण",
    },
    checklist: {
      en: [
        "No confusing tax jargon or panic",
        "Clear explanation of supported next steps",
        "Honest boundaries when professional help is needed",
      ],
      hi: [
        "कोई कानूनी उलझन या डराने वाली भाषा नहीं",
        "समर्थित अगले कदमों का स्पष्ट स्पष्टीकरण",
        "जब पेशेवर मदद चाहिए हो तो ईमानदार सीमाएं",
      ],
    },
    footerText: {
      en: "Explained in easy English and Hindi. No tax degree needed.",
      hi: "आसान हिन्दी और अंग्रेज़ी में समझें। किसी वकील की जरूरत नहीं।",
    },
    visualKind: "standard",
  },
  {
    stepNum: "03",
    badge: { en: "Checklist", hi: "चेकलिस्ट" },
    badgeColor: "#f59e0b",
    barTitle: { en: "03 Prepare · Only What's Needed", hi: "03 तैयारी · केवल जरूरी कागज़" },
    headTitle: { en: "Document Checklist", hi: "कागज़ात चेकलिस्ट" },
    headSubtitle: { en: "Keep These Ready", hi: "बस ये तैयार रखें" },
    headMeta: { en: "Evidence Required", hi: "प्रमाण आवश्यक" },
    accentColor: "#f59e0b",
    findingLabel: { en: "Keep Ready", hi: "तैयार रखें" },
    findingValue: {
      en: "Workflow-specific document checklist based on your notice type",
      hi: "आपके नोटिस प्रकार के आधार पर कार्यप्रवाह-विशिष्ट दस्तावेज़ चेकलिस्ट",
    },
    checklist: {
      en: [
        "No endless forms or repetitive questions",
        "Shows exactly which records support your response",
        "Safe 'Not sure' option if you don't know an answer",
      ],
      hi: [
        "कोई लंबे फॉर्म या बार-बार पूछे जाने वाले सवाल नहीं",
        "साफ पता चलता है कि कौन से रिकॉर्ड सबूत बनेंगे",
        "'पक्का पता नहीं' विकल्प भी सुरक्षित रूप से उपलब्ध",
      ],
    },
    footerText: {
      en: "Collect only what is asked. Never send excess files.",
      hi: "सिर्फ वही भेजें जो मांगा गया है। गैर-जरूरी फाइलें न लगाएं।",
    },
    visualKind: "evidence",
  },
  {
    stepNum: "04",
    badge: { en: "Fact-Checked", hi: "सत्यापित" },
    badgeColor: "#8b5cf6",
    barTitle: { en: "04 Review · Ready Response", hi: "04 ड्राफ्ट · बना हुआ जवाब" },
    headTitle: { en: "Your Response Draft", hi: "आपका जवाब पत्र" },
    headSubtitle: { en: "Fact-Checked & Ready", hi: "तथ्यों से सत्यापित" },
    headMeta: { en: "Ready to Edit", hi: "बदलने के लिए तैयार" },
    accentColor: "#8b5cf6",
    findingLabel: { en: "Ready Draft", hi: "तैयार जवाब" },
    findingValue: {
      en: "A workflow-specific response draft based on your answers and records",
      hi: "आपके उत्तरों और रिकॉर्ड के आधार पर कार्यप्रवाह-विशिष्ट जवाब पत्र",
    },
    checklist: {
      en: [
        "Content is based on your uploaded records and answers",
        "Easy to read and fully editable",
        "Nothing is finalized without your explicit approval",
      ],
      hi: [
        "सामग्री आपके अपलोड किए गए रिकॉर्ड और उत्तरों पर आधारित है",
        "आसानी से पढ़ें और अपनी इच्छानुसार बदलें",
        "आपकी स्पष्ट मंजूरी के बिना कुछ भी आगे नहीं बढ़ता",
      ],
    },
    footerText: {
      en: "You can edit or change any sentence before downloading.",
      hi: "डाउनलोड करने से पहले आप हर वाक्य को बदल सकते हैं।",
    },
    visualKind: "citations",
  },
  {
    stepNum: "05",
    badge: { en: "Safe Handoff", hi: "सुरक्षित" },
    badgeColor: "#10b981",
    barTitle: { en: "05 Submit · Official Portal", hi: "05 सबमिट · सरकारी पोर्टल" },
    headTitle: { en: "Official Portal Upload", hi: "सरकारी पोर्टल पर जमा करें" },
    headSubtitle: { en: "Workflow-specific navigation", hi: "कार्यप्रवाह-विशिष्ट नेविगेशन" },
    headMeta: { en: "Final Step", hi: "अंतिम कदम" },
    accentColor: "#10b981",
    findingLabel: { en: "You Stay In Full Control", hi: "पूरा नियंत्रण आपके पास" },
    findingValue: {
      en: "Download your response and follow the correct portal navigation for your notice type",
      hi: "अपना उत्तर डाउनलोड करें और अपने नोटिस प्रकार के लिए सही पोर्टल नेविगेशन का पालन करें",
    },
    checklist: {
      en: [
        "We never submit for you or ask for portal passwords",
        "Numbered PDF ready to attach with one click",
        "Step-by-step guide shows the correct portal section for your notice",
      ],
      hi: [
        "हम कभी आपके बदले सबमिट नहीं करते, न पासवर्ड मांगते हैं",
        "नंबर लगे साफ PDF अटैचमेंट तैयार",
        "आपके नोटिस के लिए सही पोर्टल अनुभाग दिखाता स्पष्ट सचित्र तरीका",
      ],
    },
    footerText: {
      en: "Tax Mitra prepares the package. You safely upload it yourself.",
      hi: "Tax Mitra फाइल तैयार करता है। अपलोड आप स्वयं सुरक्षित करते हैं।",
    },
    visualKind: "portal",
  },
];

const promises = [
  ["01", "PLAIN LANGUAGE", "Simple explanations without legal jargon."],
  ["02", "MULTI-WORKFLOW SUPPORT", "Guided paths for 142(1), 133(6), 245, 154, and more."],
  ["03", "DOCUMENT HELP", "Prepare only the documents your notice needs."],
  ["04", "HUMAN CONTROL", "You approve every important action. Safe stops when uncertain."],
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
    "Multi-workflow guided support for 142(1), 133(6), 245, 154, and more",
    "Verified knowledge base & CBDT citations",
    "Deterministic rules & dynamic questions",
    "Evidence checklist & response drafting",
    "Refuses when uncertain · Human approval gate · Safe stops",
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

  const [activeStep, setActiveStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  // Selecting a step jumps immediately to it and continues the loop
  const handleSelectStep = (index: number) => {
    setActiveStep(index);
    setIsPlaying(true);
  };

  useEffect(() => {
    if (!isPlaying) return;
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % heroSteps.length);
    }, 4500);
    return () => clearInterval(timer);
  }, [isPlaying, activeStep]);

  const curStep = heroSteps[activeStep];

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

          <ol
            className="tm-hero-flow"
            aria-label={locale === "hi" ? "नोटिस से कार्रवाई तक" : "From notice to action"}
            role="tablist"
          >
            {(locale === "hi"
              ? ["नोटिस", "समझें", "तैयार करें", "समीक्षा", "कार्रवाई"]
              : ["Notice", "Understand", "Prepare", "Review", "Act"]
            ).map((label, index) => (
              <li
                key={label}
                role="tab"
                aria-selected={activeStep === index}
                tabIndex={0}
                className={index === activeStep ? "is-active" : ""}
                onClick={() => handleSelectStep(index)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    handleSelectStep(index);
                  }
                }}
              >
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

        <aside
          className="tm-notice-preview"
          aria-label={locale === "hi" ? "टैक्स मित्रा कार्यप्रणाली एनीमेशन" : "Tax Mitra workflow animation"}
        >
          <div className="tm-preview-progress-track" aria-hidden="true">
            <div
              key={`${activeStep}-${isPlaying}`}
              className={`tm-preview-progress-bar ${!isPlaying ? "is-paused" : ""}`}
            />
          </div>

          <div className="tm-notice-preview-bar">
            <div className="tm-notice-preview-title">
              <span>{curStep.barTitle[locale === "hi" ? "hi" : "en"]}</span>
            </div>
            <div className="tm-preview-controls" aria-label={locale === "hi" ? "कदम नेविगेशन" : "Step navigation"}>
              {heroSteps.map((s, idx) => (
                <button
                  key={s.stepNum}
                  type="button"
                  className={`tm-preview-step-btn ${idx === activeStep ? "is-active" : ""}`}
                  onClick={() => handleSelectStep(idx)}
                  aria-label={`${locale === "hi" ? "कदम" : "Step"} ${idx + 1}`}
                  aria-pressed={idx === activeStep}
                >
                  {idx + 1}
                </button>
              ))}
              <button
                type="button"
                className="tm-preview-play-btn"
                onClick={() => setIsPlaying((p) => !p)}
                aria-label={
                  isPlaying
                    ? locale === "hi" ? "एनीमेशन रोकें" : "Pause animation loop"
                    : locale === "hi" ? "एनीमेशन चलाएं" : "Play animation loop"
                }
                title={isPlaying ? (locale === "hi" ? "रोकें" : "Pause loop") : (locale === "hi" ? "चलाएं" : "Play loop")}
              >
                {isPlaying ? "⏸" : "▶"}
              </button>
            </div>
            <b>
              <span
                className="tm-preview-dot"
                style={{ background: curStep.badgeColor }}
                aria-hidden="true"
              />
              {curStep.badge[locale === "hi" ? "hi" : "en"]}
            </b>
          </div>

          <div className="tm-notice-sheet" key={activeStep}>
            <div className="tm-notice-sheet-head">
              <Mark />
              <div>
                <span>{curStep.headTitle[locale === "hi" ? "hi" : "en"]}</span>
                <strong>{curStep.headSubtitle[locale === "hi" ? "hi" : "en"]}</strong>
              </div>
              <small>{curStep.headMeta[locale === "hi" ? "hi" : "en"]}</small>
            </div>

            {curStep.visualKind === "scanner" && (
              <div className="tm-notice-scanner-container" aria-hidden="true">
                <div className="tm-scan-beam" />
                <div className="tm-notice-lines">
                  <i /><i /><i /><i />
                </div>
                <div className="tm-scan-badge">
                  <span>●</span>
                  {locale === "hi" ? "दस्तावेज़ की त्वरित जांच जारी..." : "Instant Notice Scan Active..."}
                </div>
              </div>
            )}

            {curStep.visualKind === "standard" && (
              <div className="tm-notice-lines" aria-hidden="true">
                <i /><i /><i /><i />
              </div>
            )}

            {curStep.visualKind === "evidence" && (
              <div className="tm-evidence-chips" aria-label="Evidence mapping preview">
                <span className="tm-evidence-chip is-mapped">✓ {locale === "hi" ? "आवश्यक दस्तावेज़" : "Required documents"}</span>
                <span className="tm-evidence-chip is-mapped">✓ {locale === "hi" ? "आपके रिकॉर्ड" : "Your records"}</span>
                <span className="tm-evidence-chip is-needed">? {locale === "hi" ? "अतिरिक्त वैकल्पिक" : "Optional (if applicable)"}</span>
              </div>
            )}

            {curStep.visualKind === "citations" && (
              <div className="tm-citation-highlight" aria-label="Grounded draft response preview">
                <span>
                  {locale === "hi"
                    ? "आपके उत्तरों और रिकॉर्ड के आधार पर "
                    : "Based on your answers and records "}
                </span>
                <span className="tm-citation-badge">
                  {locale === "hi" ? "[आधिकारिक स्रोत से सत्यापित ✓]" : "[Official sources verified ✓]"}
                </span>
                <span>
                  {locale === "hi"
                    ? "आपकी स्थिति को सटीक रूप से प्रस्तुत किया गया है"
                    : "Your position is accurately represented."}
                </span>
              </div>
            )}

            {curStep.visualKind === "portal" && (
              <div className="tm-portal-handoff-banner" aria-label="Portal package preview">
                <span>📦 {locale === "hi" ? "आपका_टैक्स_जवाब.pdf (तैयार)" : "Your_Tax_Reply.pdf (Ready)"}</span>
                <span className="tm-portal-tag">{locale === "hi" ? "कार्यप्रवाह-विशिष्ट पोर्टल नेविगेशन" : "Workflow-specific portal navigation"}</span>
              </div>
            )}

            <div
              className="tm-notice-finding"
              style={{ borderLeftColor: curStep.accentColor }}
            >
              <span style={{ color: curStep.accentColor }}>
                {curStep.findingLabel[locale === "hi" ? "hi" : "en"]}
              </span>
              <strong>{curStep.findingValue[locale === "hi" ? "hi" : "en"]}</strong>
            </div>

            <ul className="tm-notice-checklist">
              {curStep.checklist[locale === "hi" ? "hi" : "en"].map((item, idx) => (
                <li key={idx}>
                  <span aria-hidden="true" style={{ background: curStep.accentColor }} />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <p>{curStep.footerText[locale === "hi" ? "hi" : "en"]}</p>
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
              ? "Tax Mitra विभाग की भाषा को समझने योग्य बनाता है, ज़रूरी रिकॉर्ड पहचानता है और आपकी समीक्षा के लिए एक सीमित, सुरक्षित रास्ता तैयार करता है। कई नोटिस प्रकारों के लिए कार्यप्रवाह-विशिष्ट मार्गदर्शन प्रदान करता है।"
              : "Tax Mitra translates departmental language, identifies the records that matter, and gives you a bounded path to review before you act. Supports multiple notice types with workflow-specific guidance."}
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
