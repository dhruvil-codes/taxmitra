import { ChangeEvent, DragEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, ApiError, ExtractionResult, store } from "../lib";
import { Card, PrimaryButton } from "../components";

const MAX_SIZE = 10 * 1024 * 1024;
const refusalCopy: Record<string, { en: string; hi: string }> = {
  empty_pdf: { en: "This PDF is empty. Choose the complete notice PDF.", hi: "यह PDF खाली है। पूरा नोटिस PDF चुनें।" },
  malformed_pdf: { en: "This file could not be read as a valid PDF. Download it again and retry.", hi: "इस फ़ाइल को वैध PDF के रूप में पढ़ा नहीं जा सका। इसे फिर डाउनलोड करके प्रयास करें।" },
  ocr_not_supported: { en: "This appears to be a scanned or image-only PDF. OCR is not supported in this version.", hi: "यह स्कैन या केवल-चित्र PDF लगता है। इस संस्करण में OCR समर्थित नहीं है।" },
  file_too_large: { en: "This PDF exceeds the 10 MB processing limit.", hi: "यह PDF 10 MB की प्रोसेसिंग सीमा से बड़ी है।" },
  unsupported_notice_type: { en: "This is not a supported Section 142(1) scrutiny notice.", hi: "यह समर्थित धारा 142(1) जांच नोटिस नहीं है।" },
  no_supported_requests: { en: "Tax Mitra found text, but not enough clearly numbered department requests to guide you without guessing. Try the included 142(1) demo notice or upload a notice with its request schedule visible.", hi: "Tax Mitra को टेक्स्ट मिला, लेकिन बिना अनुमान लगाए मार्गदर्शन करने के लिए पर्याप्त स्पष्ट क्रमांकित विभागीय अनुरोध नहीं मिले। शामिल 142(1) डेमो नोटिस आज़माएं या अनुरोध अनुसूची दिखाई देने वाला नोटिस अपलोड करें।" },
  grounding_below_floor: { en: "The extracted requests could not be grounded safely enough to continue.", hi: "निकाले गए अनुरोधों को आगे बढ़ने लायक सुरक्षित आधार नहीं मिला।" },
};

const unsupportedNoticeInfo: Record<string, {
  title: { en: string; hi: string };
  proceeding: { en: string; hi: string };
  context: { en: string; hi: string };
  boundaryReason: { en: string; hi: string };
  nextSteps: { en: string; hi: string };
  officialSource?: { name: { en: string; hi: string }; url: string };
}> = {
  "148": {
    title: { en: "Section 148 — Reassessment notice", hi: "धारा 148 — पुनर्मूल्यांकन नोटिस" },
    proceeding: { en: "Reassessment proceedings", hi: "पुनर्मूल्यांकन कार्यवाही" },
    context: { en: "This notice relates to reassessment proceedings where the Department has information suggesting income may have escaped assessment. Such proceedings can involve specific statutory requirements, timelines, and taxpayer rights that vary based on the assessment year and applicable tax law framework.", hi: "यह नोटिस पुनर्मूल्यांकन कार्यवाही से संबंधित है जहां विभाग को जानकारी है कि आय मूल्यांकन से बच सकती है। ऐसी कार्यवाही में विशिष्ट वैधानिक आवश्यकताएं, समयरेखा और करदाता अधिकार शामिल हो सकते हैं जो आकलन वर्ष और लागू कर कानून ढांचे के आधार पर भिन्न होते हैं।" },
    boundaryReason: { en: "Tax Mitra does not currently provide a guided response workflow for reassessment proceedings. These matters can involve complex statutory requirements and specific taxpayer rights. Tax Mitra will not guess or provide guidance without adequate supported official material.", hi: "Tax Mitra वर्तमान में पुनर्मूल्यांकन कार्यवाही के लिए मार्गदर्शित प्रतिक्रिया कार्यप्रवाह प्रदान नहीं करता है। ऐसे मामलों में जटिल वैधानिक आवश्यकताएं और विशिष्ट करदाता अधिकार शामिल हो सकते हैं। Tax Mitra पर्याप्त समर्थित आधिकारिक सामग्री के बिना अनुमान नहीं लगाएगा या मार्गदर्शन नहीं देगा।" },
    nextSteps: { en: "Review the notice for the specific information, reasons, or allegations raised by the Department. Consider consulting a chartered accountant or authorised tax practitioner for guidance on your particular circumstances.", hi: "विभाग द्वारा उठाई गई विशिष्ट जानकारी, कारण या आरोपों के लिए नोटिस की समीक्षा करें। अपनी विशिष्ट परिस्थितियों के लिए मार्गदर्शन प्राप्त करने के लिए चार्टर्ड एकाउंटेंट या अधिकृत कर अभ्यासी से परामर्श करने पर विचार करें।" },
    officialSource: { name: { en: "Income Tax Department e-Filing Help Center", hi: "आयकर विभाग e-Filing सहायता केंद्र" }, url: "https://www.incometax.gov.in/iec/helpcenter/" },
  },
  "default": {
    title: { en: "Unsupported notice type", hi: "असमर्थित नोटिस प्रकार" },
    proceeding: { en: "Other proceedings", hi: "अन्य कार्यवाही" },
    context: { en: "This notice relates to proceedings for which Tax Mitra does not currently have a guided response workflow. Different notice types involve different statutory requirements, timelines, and taxpayer rights.", hi: "यह नोटिस उन कार्यवाहियों से संबंधित है जिनके लिए Tax Mitra के पास वर्तमान में मार्गदर्शित प्रतिक्रिया कार्यप्रवाह नहीं है। विभिन्न नोटिस प्रकारों में विभिन्न वैधानिक आवश्यकताएं, समयरेखा और करदाता अधिकार शामिल होते हैं।" },
    boundaryReason: { en: "Tax Mitra does not currently provide guidance for this type of proceeding. This type of notice can involve specific statutory requirements that should not be generalized. Tax Mitra will not guess or provide unsafe guidance.", hi: "Tax Mitra वर्तमान में इस प्रकार की कार्यवाही के लिए मार्गदर्शन प्रदान नहीं करता है। इस प्रकार की नोटिस में विशिष्ट वैधानिक आवश्यकताएं शामिल हो सकती हैं जिन्हें सामान्यीकृत नहीं किया जाना चाहिए। Tax Mitra अनुमान नहीं लगाएगा या असुरक्षित मार्गदर्शन नहीं देगा।" },
    nextSteps: { en: "Review the notice carefully for the specific requirements and consult a qualified tax professional for guidance on your particular circumstances.", hi: "विशिष्ट आवश्यकताओं के लिए नोटिस का सावधानीपूर्वक अध्ययन करें और अपनी विशिष्ट परिस्थितियों के लिए मार्गदर्शन के लिए योग्य कर पेशेवर से परामर्श करें।" },
    officialSource: { name: { en: "Income Tax Department e-Filing Help Center", hi: "आयकर विभाग e-Filing सहायता केंद्र" }, url: "https://www.incometax.gov.in/iec/helpcenter/" },
  },
};
const pick = (value: Record<string, string> | undefined, locale: string) => value?.[locale] ?? value?.en ?? "";

const getUnsupportedNoticeInfo = (section: string | null | undefined) => {
  if (!section) return unsupportedNoticeInfo["default"];
  const normalizedSection = section.replace(/\s/g, "").toLowerCase();
  if (normalizedSection.includes("148")) return unsupportedNoticeInfo["148"];
  return unsupportedNoticeInfo["default"];
};

export default function Upload() {
  const { locale } = useI18n();
  const navigate = useNavigate();
  const controller = useRef<AbortController | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState("");

  useEffect(() => {
    if (!file) { setPreviewUrl(""); return; }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const choose = (candidate?: File) => {
    if (!candidate) return;
    if (candidate.type !== "application/pdf" && !candidate.name.toLowerCase().endsWith(".pdf")) { setError(locale === "hi" ? "केवल PDF फ़ाइल चुनें।" : "Choose a PDF file only."); return; }
    if (candidate.size > MAX_SIZE) { setError(locale === "hi" ? "PDF 10 MB से छोटी होनी चाहिए।" : "The PDF must be no larger than 10 MB."); return; }
    setError(""); setResult(null); setFile(candidate);
  };
  const drop = (event: DragEvent<HTMLLabelElement>) => { event.preventDefault(); setDragging(false); choose(event.dataTransfer.files[0]); };
  const dragOver = (event: DragEvent<HTMLLabelElement>) => { event.preventDefault(); setDragging(true); };
  const dragLeave = (event: DragEvent<HTMLLabelElement>) => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false); };
  const change = (event: ChangeEvent<HTMLInputElement>) => choose(event.target.files?.[0]);
  const extract = async () => {
    if (!file || uploading) return;
    controller.current?.abort(); controller.current = new AbortController(); setUploading(true); setError(""); setResult(null);
    try { setResult(await api.extractScrutiny(file, controller.current.signal)); }
    catch (e) {
      if ((e as Error).name !== "AbortError") {
        if (import.meta.env.DEV) {
          console.error("Extraction error:", e);
        }
        setError(e instanceof ApiError ? e.message : (locale === "hi" ? "सेवा उपलब्ध नहीं है। फिर प्रयास करें।" : "The extraction service is unavailable. Try again."));
      }
    }
    finally { setUploading(false); }
  };
  const confirm = async (confirmed: boolean) => {
    if (!result?.extraction_id || !result.fingerprint || confirming) return;
    setConfirming(true); setError("");
    try {
      const response = await api.confirmExtraction(result.extraction_id, result.fingerprint, confirmed);
      if (!response.supported || !response.notice_id) { setResult(null); setFile(null); setError(locale === "hi" ? "पुष्टि नहीं की गई। सही PDF चुनकर फिर शुरू करें।" : "The extraction was not confirmed. Choose the correct PDF and start again."); return; }
      store.setUploadedNoticeId(response.notice_id); store.setExtractionConfirmed(response.notice_id, true); store.setScrutinyStage(response.notice_id, "requests");
      navigate(`/notices/${response.notice_id}/scrutiny`, { state: { uploaded: true } });
    } catch (e) {
      if (import.meta.env.DEV) {
        console.error("Confirmation error:", e);
      }
      setError(e instanceof ApiError && e.status === 409 ? (locale === "hi" ? "निष्कर्षण सत्र अमान्य या समाप्त हो गया। PDF फिर से अपलोड करें।" : "The extraction session is invalid or expired. Upload the PDF again.") : e instanceof ApiError ? e.message : (locale === "hi" ? "पुष्टि नहीं हो सकी।" : "Confirmation failed."));
    }
    finally { setConfirming(false); }
  };
  const reset = () => { controller.current?.abort(); setFile(null); setResult(null); setError(""); setUploading(false); };
  const refused = result && !result.supported;

  return <div className="app-page upload-page">
    <p className="app-eyebrow">[ TM / UPLOAD / NOTICE ]</p>
    <h1 className="app-title">{locale === "hi" ? "अपना कर नोटिस अपलोड करें।" : "Upload your tax notice."}</h1>
    <p className="app-lead">{locale === "hi" ? "साधारण टेक्स्ट वाली धारा 142(1) PDF अपलोड करें। Tax Mitra अधिकारी के हर अनुरोध को अलग करेगा, लेकिन आपके मिलान और पुष्टि के बाद ही मार्गदर्शन खुलेगा।" : "Upload a text-based Section 142(1) PDF. Tax Mitra separates every request from the officer, but guidance opens only after you match and confirm the extraction."}</p>
    <ol className="upload-process" aria-label={locale === "hi" ? "दस्तावेज़ प्रक्रिया" : "Document process"}>
      <li className={!result ? "is-current" : "is-done"}><span>01</span><strong>{locale === "hi" ? "पढ़ें" : "READ"}</strong></li>
      <li className={result ? "is-current" : ""}><span>02</span><strong>{locale === "hi" ? "जाँचें" : "CHECK"}</strong></li>
      <li><span>03</span><strong>{locale === "hi" ? "पुष्टि" : "CONFIRM"}</strong></li>
      <li><span>04</span><strong>{locale === "hi" ? "मार्गदर्शन" : "GUIDE"}</strong></li>
    </ol>

    {!result && <><label className={`upload-zone${dragging ? " is-dragging" : ""}${uploading ? " is-processing" : ""}`} onDragEnter={dragOver} onDragOver={dragOver} onDragLeave={dragLeave} onDrop={drop}>
      <input type="file" accept="application/pdf,.pdf" onChange={change} disabled={uploading} />
      <span className="upload-icon">{uploading ? "···" : "PDF"}</span><strong>{dragging ? (locale === "hi" ? "PDF यहाँ छोड़ें" : "Release to choose this PDF") : (locale === "hi" ? "PDF यहाँ छोड़ें या चुनें" : "Drop a PDF here or choose a file")}</strong><small>{locale === "hi" ? "अधिकतम 10 MB · केवल टेक्स्ट PDF · OCR नहीं" : "Maximum 10 MB · text PDFs only · no OCR"}</small>
    </label>
    {file && <div className="upload-receipt">
      <Card className="upload-file"><div><p className="app-section-label">[ DOCUMENT RECEIVED ]</p><strong>{file.name}</strong><small>PDF · {(file.size / 1024 / 1024).toFixed(2)} MB · {locale === "hi" ? "जाँच के लिए तैयार" : "READY TO INSPECT"}</small></div><button onClick={reset} disabled={uploading}>{locale === "hi" ? "हटाएँ" : "REMOVE"}</button></Card>
      {previewUrl && <section className="pdf-preview" aria-label={locale === "hi" ? "चुनी गई PDF का पूर्वावलोकन" : "Selected PDF preview"}><object data={previewUrl} type="application/pdf"><p>{locale === "hi" ? "इस ब्राउज़र में PDF पूर्वावलोकन उपलब्ध नहीं है।" : "PDF preview is unavailable in this browser."}</p></object></section>}
    </div>}
    {uploading && <section className="extraction-status" aria-live="polite"><span className="status-pulse"/><div><p className="app-section-label">[ EXTRACTION IN PROGRESS ]</p><h2>{locale === "hi" ? "आपका नोटिस पढ़ा जा रहा है" : "Reading your notice"}</h2><p>{locale === "hi" ? "दस्तावेज़ मिल गया है। क्रमांकित अनुरोध और आधार निकाले जा रहे हैं।" : "Document received. Numbered requests and their grounding are being extracted."}</p></div></section>}
    <div className="upload-actions">{file && <PrimaryButton onClick={extract} disabled={uploading}>{uploading ? (locale === "hi" ? "पढ़ा जा रहा है…" : "READING PDF…") : (locale === "hi" ? "अन��रोध निकालें" : "EXTRACT REQUESTS")} →</PrimaryButton>}{uploading && <button className="app-back !mt-0" onClick={()=>controller.current?.abort()}>{locale === "hi" ? "रोकें" : "CANCEL"}</button>}<Link className="app-back !mt-0" to="/">← {locale === "hi" ? "होम" : "HOME"}</Link></div></>}

    {result?.supported && <section aria-labelledby="review-title">
      <p className="app-section-label">[ EXTRACTION NEEDS CONFIRMATION ]</p><h2 id="review-title" className="question-title">{locale === "hi" ? "मूल PDF से हर अनुरोध मिलाएँ" : "Match every request to the original PDF"}</h2>
      <div className="scrutiny-meta"><span>{result.metadata.section ?? "—"}</span><span>AY {result.metadata.assessment_year ?? "—"}</span><span>{result.metadata.notice_reference ?? "—"}</span><span>{result.metadata.response_deadline ?? "—"}</span></div>
      <p className="app-body">{locale === "hi" ? `निष्कर्षण विश्वास ${Math.round(result.extraction.confidence*100)}% · आधार विश्वास ${Math.round(result.grounding.confidence*100)}%` : `Extraction confidence ${Math.round(result.extraction.confidence*100)}% · grounding confidence ${Math.round(result.grounding.confidence*100)}%`}</p>
      {[...result.extraction.warnings, ...result.requests.flatMap(r=>r.warnings)].map((warning,i)=><div className="notice-boundary" key={i}><p className="app-section-label">[ REVIEW WARNING ]</p><p className="app-body">{warning}</p></div>)}
      <p className="request-count">{String(result.requests.length).padStart(2,"0")} {locale === "hi" ? "अनुरोध मिले" : "REQUESTS FOUND"}</p>
      <div className="document-requests">{result.requests.map((request,index)=><details className="document-request" key={request.request_id} open={index===0}><summary><span>{String(index+1).padStart(2,"0")}</span><strong>{request.original_text}</strong><i>{locale === "hi" ? "खोलें" : "OPEN"}</i></summary><div className="document-request-body"><div className="official-wording"><b>{locale === "hi" ? "अधिकारी के मूल शब्द" : "OFFICIAL REQUEST WORDING"}</b><blockquote>{request.original_text}</blockquote></div><div className="scrutiny-explain"><div><b>{locale === "hi" ? "Tax Mitra की आसान भाषा" : "TAX MITRA EXPLANATION"}</b><p>{pick(request.plain_language_explanation,locale)}</p></div><div><b>{locale === "hi" ? "क्यों माँगा गया" : "WHY REQUIRED"}</b><p>{pick(request.why_required,locale) || request.response_section}</p></div></div>{request.required_evidence.length>0&&<div className="request-evidence"><b>{locale === "hi" ? "संभावित रिकॉर्ड" : "POSSIBLE RECORDS"}</b><ul>{request.required_evidence.map((item,i)=><li key={i}>{pick(item,locale)}</li>)}</ul></div>}<div className="request-grounding"><span>{request.classification_id}</span><span>{locale === "hi" ? "अनुरोध विश्वास" : "REQUEST CONFIDENCE"} {Math.round(request.confidence*100)}%</span><span>{request.grounding.method} {Math.round(request.grounding.confidence*100)}%</span></div>{request.warnings.map((warning,i)=><p className="request-warning" key={i}>{warning}</p>)}{request.citations.map(c=><a key={c.id} className="scrutiny-source" href={c.official_url} target="_blank" rel="noreferrer">{c.source_name} · {c.section} ↗</a>)}</div></details>)}</div>
      <div className="human-check"><p className="app-section-label">[ HUMAN CHECK / 02 ]</p><p className="app-body">{locale === "hi" ? "पुष्टि तभी करें जब सूची PDF से पूरी तरह मेल खाती हो। PDF bytes memory में process होते हैं, store या log नहीं होते; session 30 मिनट में समाप्त होता है।" : "Confirm only if this list matches the PDF. PDF bytes are processed in memory and are not stored or logged; the session expires after 30 minutes."}</p></div>
      <div className="confirmation-actions"><PrimaryButton onClick={()=>confirm(true)} disabled={confirming}>{confirming ? (locale === "hi" ? "पुष्टि हो रही है…" : "CONFIRMING…") : (locale === "hi" ? "हाँ, सूची सही है" : "YES, THE LIST MATCHES")} →</PrimaryButton><button onClick={()=>confirm(false)} disabled={confirming}>{locale === "hi" ? "नहीं, फिर से शुरू करें" : "NO, START AGAIN"}</button></div>
    </section>}

    {refused && (() => {
      const info = getUnsupportedNoticeInfo(result.metadata.section);
      return <section className="app-empty" role="alert">
        <p className="app-section-label">[ SAFE STOP / {result.extraction.refusal_reason ?? "UNCLASSIFIED"} ]</p>
        <h2 className="question-title">{pick(info.title, locale)}</h2>
        <p className="app-lead">{pick(info.proceeding, locale)}</p>
        <p className="app-body">{pick(info.context, locale)}</p>
        <div className="notice-boundary">
          <p className="app-section-label">[ WHY WE'RE STOPPING ]</p>
          <p className="app-body">{pick(info.boundaryReason, locale)}</p>
        </div>
        <div className="notice-boundary">
          <p className="app-section-label">[ WHAT YOU CAN DO NEXT ]</p>
          <p className="app-body">{pick(info.nextSteps, locale)}</p>
        </div>
        {info.officialSource && <a href={info.officialSource.url} target="_blank" rel="noopener noreferrer" className="scrutiny-source">
          {pick(info.officialSource.name, locale)} ↗
        </a>}
        {result.extraction.warnings.map((w,i)=><p key={i} className="text-sm text-stone-600 mt-2">{w}</p>)}
        <div className="confirmation-actions">
          {info.officialSource && <a href={info.officialSource.url} target="_blank" rel="noopener noreferrer" className="app-primary">{locale === "hi" ? "आधिकारिक मार्गदर्शन देखें" : "View official guidance"} ↗</a>}
          <button onClick={() => navigate("/login")}>{locale === "hi" ? "कार्यशील 142(1) डेमो इस्तेमाल करें" : "Use the working 142(1) demo"}</button>
          <button onClick={reset}>{locale === "hi" ? "दूसरी PDF चुनें" : "Choose another PDF"}</button>
        </div>
      </section>;
    })()}
    {error && <p className="upload-error" role="alert">{error}</p>}
    <div className="notice-boundary"><p className="app-section-label">[ PROCESSING BOUNDARY ]</p><p className="app-body">{locale === "hi" ? "केवल साधारण टेक्स्ट PDF समर्थित हैं। OCR नहीं है। Tax Mitra कुछ भी जमा नहीं करता और निकाले गए तथ्य आपकी पुष्टि से पहले विश्वसनीय नहीं माने जाते।" : "Only ordinary text PDFs are supported; OCR is not. Tax Mitra submits nothing, and extracted facts are not trusted until you confirm them."}</p></div>
  </div>;
}
