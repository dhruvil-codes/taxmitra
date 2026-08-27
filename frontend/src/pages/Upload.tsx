import { ChangeEvent, DragEvent, useRef, useState } from "react";
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
  no_supported_requests: { en: "No supported numbered scrutiny requests were found, so Tax Mitra will not guess.", hi: "कोई समर्थित क्रमांकित जांच अनुरोध नहीं मिला, इसलिए Tax Mitra अनुमान नहीं लगाएगा।" },
  grounding_below_floor: { en: "The extracted requests could not be grounded safely enough to continue.", hi: "निकाले गए अनुरोधों को आगे बढ़ने लायक सुरक्षित आधार नहीं मिला।" },
};
const pick = (value: Record<string, string> | undefined, locale: string) => value?.[locale] ?? value?.en ?? "";

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
    catch (e) { if ((e as Error).name !== "AbortError") setError(e instanceof ApiError ? e.detail : (locale === "hi" ? "सेवा उपलब्ध नहीं है। फिर प्रयास करें।" : "The extraction service is unavailable. Try again.")); }
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
    } catch (e) { setError(e instanceof ApiError && e.status === 409 ? (locale === "hi" ? "निष्कर्षण सत्र अमान्य या समाप्त हो गया। PDF फिर से अपलोड करें।" : "The extraction session is invalid or expired. Upload the PDF again.") : e instanceof ApiError ? e.detail : (locale === "hi" ? "पुष्टि नहीं हो सकी।" : "Confirmation failed.")); }
    finally { setConfirming(false); }
  };
  const reset = () => { controller.current?.abort(); setFile(null); setResult(null); setError(""); setUploading(false); };
  const refused = result && !result.supported;

  return <div className="app-page upload-page">
    <p className="app-eyebrow">[ UPLOAD / NOTICE ]</p>
    <h1 className="app-title">{locale === "hi" ? "अपना PDF यहाँ छोड़ें" : "Drop your PDF here"}</h1>
    <p className="app-lead">{locale === "hi" ? "साधारण टेक्स्ट वाली धारा 142(1) PDF अपलोड करें। Tax Mitra अनुरोध निकालेगा—आपकी पुष्टि के बाद ही मार्गदर्शन खुलेगा।" : "Upload an ordinary text-based Section 142(1) PDF. Tax Mitra extracts the requests—guidance unlocks only after your confirmation."}</p>

    {!result && <><label className={`upload-zone${dragging ? " is-dragging" : ""}${uploading ? " is-processing" : ""}`} onDragEnter={dragOver} onDragOver={dragOver} onDragLeave={dragLeave} onDrop={drop}>
      <input type="file" accept="application/pdf,.pdf" onChange={change} disabled={uploading} />
      <span className="upload-icon">{uploading ? "···" : "PDF"}</span><strong>{dragging ? (locale === "hi" ? "PDF यहाँ छोड़ें" : "Release to choose this PDF") : (locale === "hi" ? "PDF यहाँ छोड़ें या चुनें" : "Drop a PDF here or choose a file")}</strong><small>{locale === "hi" ? "अधिकतम 10 MB · केवल टेक्स्ट PDF · OCR नहीं" : "Maximum 10 MB · text PDFs only · no OCR"}</small>
    </label>
    {file && <Card className="upload-file"><div><p className="app-section-label">[ READY TO PROCESS ]</p><strong>{file.name}</strong><small>{(file.size / 1024 / 1024).toFixed(2)} MB</small></div><button onClick={reset} disabled={uploading}>{locale === "hi" ? "हटाएँ" : "REMOVE"}</button></Card>}
    <div className="upload-actions">{file && <PrimaryButton onClick={extract} disabled={uploading}>{uploading ? (locale === "hi" ? "पढ़ा जा रहा है…" : "READING PDF…") : (locale === "hi" ? "अनुरोध निकालें" : "EXTRACT REQUESTS")} →</PrimaryButton>}{uploading && <button className="app-back !mt-0" onClick={()=>controller.current?.abort()}>{locale === "hi" ? "रोकें" : "CANCEL"}</button>}<Link className="app-back !mt-0" to="/">← {locale === "hi" ? "होम" : "HOME"}</Link></div></>}

    {result?.supported && <section aria-labelledby="review-title">
      <p className="app-section-label">[ EXTRACTION NEEDS CONFIRMATION ]</p><h2 id="review-title" className="question-title">{locale === "hi" ? "मूल PDF से हर अनुरोध मिलाएँ" : "Match every request to the original PDF"}</h2>
      <div className="scrutiny-meta"><span>{result.metadata.section ?? "—"}</span><span>AY {result.metadata.assessment_year ?? "—"}</span><span>{result.metadata.notice_reference ?? "—"}</span><span>{result.metadata.response_deadline ?? "—"}</span></div>
      <p className="app-body">{locale === "hi" ? `निष्कर्षण विश्वास ${Math.round(result.extraction.confidence*100)}% · आधार विश्वास ${Math.round(result.grounding.confidence*100)}%` : `Extraction confidence ${Math.round(result.extraction.confidence*100)}% · grounding confidence ${Math.round(result.grounding.confidence*100)}%`}</p>
      {[...result.extraction.warnings, ...result.requests.flatMap(r=>r.warnings)].map((warning,i)=><div className="notice-boundary" key={i}><p className="app-section-label">[ REVIEW WARNING ]</p><p className="app-body">{warning}</p></div>)}
      <div className="scrutiny-list">{result.requests.map((request,index)=><Card key={request.request_id}><p className="app-section-label">[ REQUEST {String(index+1).padStart(2,"0")} / {request.classification_id} ]</p><blockquote>{request.original_text}</blockquote><div className="scrutiny-explain"><div><b>{locale === "hi" ? "आसान भाषा" : "Plain language"}</b><p>{pick(request.plain_language_explanation,locale)}</p></div><div><b>{locale === "hi" ? "उत्तर खंड" : "Response section"}</b><p>{request.response_section}</p></div></div><p className="app-body">{locale === "hi" ? "विश्वास" : "Confidence"}: {Math.round(request.confidence*100)}% · {request.grounding.method} {Math.round(request.grounding.confidence*100)}%</p>{request.citations.map(c=><a key={c.id} className="scrutiny-source" href={c.official_url} target="_blank" rel="noreferrer">{c.source_name} · {c.section} ↗</a>)}</Card>)}</div>
      <div className="notice-boundary"><p className="app-section-label">[ HUMAN CHECKPOINT ]</p><p className="app-body">{locale === "hi" ? "पुष्टि तभी करें जब सूची PDF से पूरी तरह मेल खाती हो। PDF bytes memory में process होते हैं, store या log नहीं होते; session 30 मिनट में समाप्त होता है।" : "Confirm only if this list matches the PDF. PDF bytes are processed in memory and are not stored or logged; the session expires after 30 minutes."}</p></div>
      <div className="confirmation-actions"><PrimaryButton onClick={()=>confirm(true)} disabled={confirming}>{confirming ? (locale === "hi" ? "पुष्टि हो रही है…" : "CONFIRMING…") : (locale === "hi" ? "हाँ, सूची सही है" : "YES, THE LIST MATCHES")} →</PrimaryButton><button onClick={()=>confirm(false)} disabled={confirming}>{locale === "hi" ? "नहीं, फिर से शुरू करें" : "NO, START AGAIN"}</button></div>
    </section>}

    {refused && <section className="app-empty" role="alert"><p className="app-section-label">[ SAFE STOP / {result.extraction.refusal_reason ?? "UNCLASSIFIED"} ]</p><h2 className="question-title">{locale === "hi" ? "हम इस PDF से सुरक्षित मार्गदर्शन नहीं दे सकते" : "We cannot safely guide from this PDF"}</h2><p>{refusalCopy[result.extraction.refusal_reason ?? ""]?.[locale] ?? (locale === "hi" ? "नोटिस को पर्याप्त विश्वास से पढ़ा या वर्गीकृत नहीं किया जा सका।" : "The notice could not be read or classified with sufficient confidence.")}</p>{result.extraction.warnings.map((w,i)=><p key={i}>{w}</p>)}<button className="app-primary mt-5" onClick={reset}>{locale === "hi" ? "दूसरी PDF चुनें" : "CHOOSE ANOTHER PDF"}</button></section>}
    {error && <p className="upload-error" role="alert">{error}</p>}
    <div className="notice-boundary"><p className="app-section-label">[ PROCESSING BOUNDARY ]</p><p className="app-body">{locale === "hi" ? "केवल साधारण टेक्स्ट PDF समर्थित हैं। OCR नहीं है। Tax Mitra कुछ भी जमा नहीं करता और निकाले गए तथ्य आपकी पुष्टि से पहले विश्वसनीय नहीं माने जाते।" : "Only ordinary text PDFs are supported; OCR is not. Tax Mitra submits nothing, and extracted facts are not trusted until you confirm them."}</p></div>
  </div>;
}
