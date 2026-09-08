import { ChangeEvent, DragEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, ApiError, UniversalExtractionResult, store } from "../lib";
import { Card, GuidedInteraction, PrimaryButton, WorkflowLayout } from "../components";
import { requestTitle } from "../components/UniversalWorkflow";

const MAX_SIZE = 10 * 1024 * 1024;
export function uploadRoute(classification: { frontend_entry?: string; supported: boolean; status: string; capability?: string }): "journey" | "safe-stop" {
  if (classification.status === "safe_stop" || classification.capability === "SAFE_STOP" || classification.frontend_entry === "unsupported") return "safe-stop";
  return "journey";
}
const refusalCopy: Record<string, { en: string; hi: string }> = {
  empty_pdf: { en: "This PDF is empty. Choose the complete notice PDF.", hi: "यह PDF खाली है। पूरा नोटिस PDF चुनें।" },
  malformed_pdf: { en: "This file could not be read as a valid PDF. Download it again and retry.", hi: "इस फ़ाइल को वैध PDF के रूप में पढ़ा नहीं जा सका। इसे फिर डाउनलोड करके प्रयास करें।" },
  ocr_not_supported: { en: "This appears to be a scanned or image-only PDF. Scanned PDFs are not supported in this version.", hi: "यह स्कैन या केवल-चित्र PDF लगता है। स्कैन PDF इस संस्करण में समर्थित नहीं है।" },
  ocr_failure: { en: "The PDF appears to be scanned, but text could not be read reliably. No text was invented.", hi: "यह PDF स्कैन की हुई लगती है, लेकिन इसे विश्वसनीय रूप से पढ़ा नहीं जा सका। कोई टेक्स्ट अनुमान से नहीं जोड़ा गया है।" },
  password_protected_pdf: { en: "This PDF is password-protected. Remove the password or upload an accessible copy.", hi: "यह PDF पासवर्ड से सुरक्षित है। पासवर्ड हटाकर या बिना पासवर्ड वाली प्रति अपलोड करें।" },
  invalid_file_type: { en: "Only PDF files are accepted.", hi: "केवल PDF फ़ाइलें स्वीकार की जाती हैं।" },
  invalid_pdf: { en: "This file is not a readable PDF.", hi: "यह फ़ाइल पढ़ने योग्य PDF नहीं है।" },
  low_extraction_confidence: { en: "The text could not be extracted clearly enough to continue safely.", hi: "टेक्स्ट को सुरक्षित रूप से आगे बढ़ने के लिए पर्याप्त स्पष्टता के साथ नहीं निकाला जा सका।" },
  missing_critical_information: { en: "The notice does not contain enough clearly numbered requests to continue without guessing.", hi: "अनुमान लगाए बिना आगे बढ़ने के लिए नोटिस में पर्याप्त स्पष्ट क्रमांकित अनुरोध नहीं हैं।" },
  file_too_large: { en: "This PDF exceeds the 10 MB processing limit.", hi: "यह PDF 10 MB की प्रोसेसिंग सीमा से बड़ी है।" },
  unsupported_notice_type: { en: "Tax Mitra identified an Income Tax communication outside the available guided workflow.", hi: "Tax Mitra ने ऐसे आयकर संचार की पहचान की जिसके लिए निर्देशित कार्यप्रवाह उपलब्ध नहीं है।" },
  no_supported_requests: { en: "Tax Mitra found text, but not enough clearly grounded requests to guide you without guessing. Review the extracted pages and consult a qualified professional if needed.", hi: "Tax Mitra को पाठ मिला, लेकिन बिना अनुमान के मार्गदर्शन के लिए पर्याप्त स्पष्ट अनुरोध नहीं मिले। निकाले गए पृष्ठों की समीक्षा करें और आवश्यकता होने पर योग्य पेशेवर से सलाह लें।" },
  grounding_below_floor: { en: "The extracted requests could not be grounded safely enough to continue.", hi: "निकाले गए अनुरोधों को आगे बढ़ने लायक सुरक्षित आधार नहीं मिला।" },
  not_income_tax_document: { en: "This document is not an Income Tax notice. Please upload your official tax notice.", hi: "यह दस्तावेज़ आयकर नोटिस नहीं है। कृपया अपना आधिकारिक कर नोटिस अपलोड करें।" },
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
    context: { en: "This notice relates to reassessment proceedings where the Department has information suggesting income may have escaped assessment. For assessment years beginning before April 1, 2026, this proceeding is governed by Section 148 of the Income-tax Act, 1961.", hi: "यह नोटिस पुनर्मूल्यांकन कार्यवाही से संबंधित है जहां विभाग को जानकारी है कि आय मूल्यांकन से बच सकती है। 1 अप्रैल 2026 से पहले शुरू होने वाले आकलन वर्षों के लिए, यह कार्यवाही आयकर अधिनियम, 1961 की धारा 148 के तहत शासित है।" },
    boundaryReason: { en: "Tax Mitra does not currently provide a guided response workflow for reassessment proceedings. These matters can involve complex statutory requirements and specific taxpayer rights. Tax Mitra will not guess or provide guidance without adequate supported official material.", hi: "Tax Mitra वर्तमान में पुनर्मूल्यांकन कार्यवाही के लिए मार्गदर्शित प्रतिक्रिया कार्यप्रवाह प्रदान नहीं करता है। ऐसे मामलों में जटिल वैधानिक आवश्यकताएं और विशिष्ट करदाता अधिकार शामिल हो सकते हैं। Tax Mitra पर्याप्त समर्थित आधिकारिक सामग्री के बिना अनुमान नहीं लगाएगा या मार्गदर्शन नहीं देगा।" },
    nextSteps: { en: "Review the notice for the specific information, reasons, or allegations raised by the Department. Consider consulting a chartered accountant or authorised tax practitioner for guidance on your particular circumstances.", hi: "विभाग द्वारा उठाई गई विशिष्ट जानकारी, कारण या आरोपों के लिए नोटिस की समीक्षा करें। अपनी विशिष्ट परिस्थितियों के लिए मार्गदर्शन प्राप्त करने के लिए चार्टर्ड एकाउंटेंट या अधिकृत कर अभ्यासी से परामर्श करने पर विचार करें।" },
    officialSource: { name: { en: "Income Tax Department e-Filing Help Center", hi: "आयकर विभाग e-Filing सहायता केंद्र" }, url: "https://www.incometax.gov.in/iec/helpcenter/" },
  },
  "148a": {
    title: { en: "Section 148A — Show Cause Notice", hi: "धारा 148A — कारण बताओ नोटिस" },
    proceeding: { en: "Reassessment inquiry under Section 148A", hi: "धारा 148A के तहत पुनर्मूल्यांकन जांच" },
    context: { en: "This is a show-cause inquiry prior to reassessment under Section 148A of the Income-tax Act.", hi: "यह आयकर अधिनियम की धारा 148A के तहत पुनर्मूल्यांकन से पूर्व कारण बताओ जांच है।" },
    boundaryReason: { en: "Automating Section 148A replies without factual audit can forfeit crucial legal defenses. Tax Mitra safe-stops to protect taxpayer rights.", hi: "तथ्यात्मक ऑडिट के बिना धारा 148A के जवाब स्वचालित करना कानूनी अधिकारों को प्रभावित कर सकता है।" },
    nextSteps: { en: "Review the flagged information on the Compliance Portal and submit a substantiated response with professional assistance.", hi: "अनुपालन पोर्टल पर चिह्नित जानकारी की समीक्षा करें और पेशेवर सहायता से जवाब प्रस्तुत करें।" },
    officialSource: { name: { en: "Income Tax Department e-Filing Help Center", hi: "आयकर विभाग e-Filing सहायता केंद्र" }, url: "https://www.incometax.gov.in/iec/helpcenter/" },
  },
  "131": {
    title: { en: "Section 131 — Summons", hi: "धारा 131 — समन" },
    proceeding: { en: "Summons under Section 131", hi: "धारा 131 के तहत समन" },
    context: { en: "This communication is a statutory summons requiring personal attendance or production of specific records.", hi: "यह एक वैधानिक समन है जिसमें व्यक्तिगत उपस्थिति या विशिष्ट रिकॉर्ड प्रस्तुत करने की आवश्यकता होती है।" },
    boundaryReason: { en: "Summons under Section 131 carry judicial proceedings powers and cannot be answered via automated questionnaires.", hi: "समन कार्यवाही में न्यायिक शक्तियां होती हैं और इन्हें स्वचालित प्रश्नावली से हल नहीं किया जा सकता।" },
    nextSteps: { en: "Comply within the summoned date and engage an authorized tax representative.", hi: "समन की तारीख के भीतर पालन करें और अधिकृत कर प्रतिनिधि से संपर्क करें।" },
    officialSource: { name: { en: "Income Tax Department e-Filing Help Center", hi: "आयकर विभाग e-Filing सहायता केंद्र" }, url: "https://www.incometax.gov.in/iec/helpcenter/" },
  },
  "not_income_tax": {
    title: { en: "This document is not an Income Tax notice", hi: "यह दस्तावेज़ आयकर नोटिस नहीं है" },
    proceeding: { en: "Unrecognized document", hi: "अपरिचित गैर-आयकर दस्तावेज़" },
    context: { en: "The uploaded PDF does not contain any Income Tax Department notice headers, statutory section references (e.g. 142(1), 143(1), 148, 139(9)), or official Department identifiers.", hi: "अपलोड की गई PDF में आयकर विभाग का नोटिस हेडर, वैधानिक धारा संदर्भ (उदा. 142(1), 143(1), 148, 139(9)) या आधिकारिक विभाग पहचानकर्ता नहीं मिले।" },
    boundaryReason: { en: "Tax Mitra only processes official Income Tax Department communications. Processing unrelated documents could lead to incorrect guidance.", hi: "Tax Mitra केवल आयकर विभाग के आधिकारिक संचार को प्रोसेस करता है। असंबद्ध दस्तावेज़ों पर मार्गदर्शन देना असुरक्षित है।" },
    nextSteps: { en: "Please upload an official notice issued by the Income Tax Department to continue.", hi: "आगे बढ़ने के लिए कृपया आयकर विभाग द्वारा जारी आधिकारिक नोटिस अपलोड करें।" },
    officialSource: { name: { en: "Income Tax Department e-Filing Portal", hi: "आयकर विभाग ई-फाइलिंग पोर्टल" }, url: "https://www.incometax.gov.in" },
  },

  "low_confidence": {
    title: { en: "Illegible Scan", hi: "अपठनीय स्कैन" },
    proceeding: { en: "Unreadable scan — safe stop", hi: "अपठनीय स्कैन — सुरक्षित ठहराव" },
    context: { en: "The uploaded notice scan could not be read clearly enough to safely identify statutory requests.", hi: "अपलोड किए गए नोटिस स्कैन को सुरक्षित रूप से पढ़ने के लिए पर्याप्त स्पष्टता नहीं मिली।" },
    boundaryReason: { en: "Tax Mitra never guesses notice contents. Proceeding without legible text could lead to inaccurate responses.", hi: "Tax Mitra कभी भी नोटिस की सामग्री का अनुमान नहीं लगाता।" },
    nextSteps: { en: "Download the original digital PDF notice directly from the Income Tax e-Filing portal, or scan at 300+ DPI.", hi: "आयकर ई-फाइलिंग पोर्टल से मूल डिजिटल PDF डाउनलोड करें, या 300+ DPI पर पुनः स्कैन करें।" },
    officialSource: { name: { en: "Income Tax Department e-Filing Help Center", hi: "आयकर विभाग e-Filing सहायता केंद्र" }, url: "https://www.incometax.gov.in/iec/helpcenter/" },
  },
  "default": {
    title: { en: "Income Tax Department Communication", hi: "आयकर विभाग संचार" },
    proceeding: { en: "Income Tax communication — unclassified proceeding", hi: "आयकर संचार — अनिर्दिष्ट कार्यवाही" },
    context: { en: "This notice relates to proceedings for which Tax Mitra does not currently have a guided response workflow. Different notice types involve different statutory requirements, timelines, and taxpayer rights.", hi: "यह नोटिस उन कार्यवाहियों से संबंधित है जिनके लिए Tax Mitra के पास वर्तमान में मार्गदर्शित प्रतिक्रिया कार्यप्रवाह नहीं है। विभिन्न नोटिस प्रकारों में विभिन्न वैधानिक आवश्यकताएं, समयरेखा और करदाता अधिकार शामिल होते हैं।" },
    boundaryReason: { en: "Tax Mitra does not currently provide guidance for this type of proceeding. This type of notice can involve specific statutory requirements that should not be generalized. Tax Mitra will not guess or provide unsafe guidance.", hi: "Tax Mitra वर्तमान में इस प्रकार की कार्यवाही के लिए मार्गदर्शन प्रदान नहीं करता है। इस प्रकार की नोटिस में विशिष्ट वैधानिक आवश्यकताएं शामिल हो सकती हैं जिन्हें सामान्यीकृत नहीं किया जाना चाहिए। Tax Mitra अनुमान नहीं लगाएगा या असुरक्षित मार्गदर्शन नहीं देगा।" },
    nextSteps: { en: "Review the notice carefully for the specific requirements and consult a qualified tax professional for guidance on your particular circumstances.", hi: "विशिष्ट आवश्यकताओं के लिए नोटिस का सावधानीपूर्वक अध्ययन करें और अपनी विशिष्ट परिस्थितियों के लिए मार्गदर्शन के लिए योग्य कर पेशेवर से परामर्श करें।" },
    officialSource: { name: { en: "Income Tax Department e-Filing Help Center", hi: "आयकर विभाग e-Filing सहायता केंद्र" }, url: "https://www.incometax.gov.in/iec/helpcenter/" },
  },
};
const pick = (value: Record<string, string> | undefined, locale: string) => value?.[locale] ?? value?.en ?? "";

export const filterInternalMetadata = (text: string | null | undefined): boolean => {
  if (!text) return false;
  const internalPatterns = [
    "classification_id", "request_id", "extraction_id", "fingerprint",
    "provider", "lexical", "deterministic", "confidence",
    "workflow_id", "workflow status", "grounding_status", "capability",
    "SAFE_STOP", "PARTIAL_SUPPORT", "EXPLANATION_ONLY", "SUPPORTED",
    "OCR", "ocr", "AI", "ai", "backend", "routing", "evidence routing",
    "method:", "sha256", "internal", "implementation",
    "AI classification is unavailable",
    "deterministic evidence routing was used",
    "Retrieval and guidance are intentionally deferred",
    "No section reference was confidently extracted"
  ];
  const containsInternal = internalPatterns.some(pattern => text.toLowerCase().includes(pattern.toLowerCase()));
  return !containsInternal;
};

const getUnsupportedNoticeInfo = (
  section: string | null | undefined,
  refusalReason?: string | null,
  category?: string | null
) => {
  if (refusalReason === "not_income_tax_document" || category === "not_income_tax_document") {
    return unsupportedNoticeInfo["not_income_tax"];
  }
  if (
    refusalReason === "low_extraction_confidence" ||
    refusalReason === "illegible_scan" ||
    refusalReason === "ocr_failure" ||
    refusalReason === "ocr_not_supported"
  ) {
    return unsupportedNoticeInfo["low_confidence"];
  }
  const normalizedSection = (section || "").replace(/\s/g, "").toLowerCase();
  const normalizedCat = (category || "").toLowerCase();
  if (normalizedSection.includes("148a") || normalizedCat.includes("148a")) return unsupportedNoticeInfo["148a"];
  if (normalizedSection.includes("148") || normalizedCat.includes("148")) return unsupportedNoticeInfo["148"];
  if (normalizedSection.includes("131") || normalizedCat.includes("131")) return unsupportedNoticeInfo["131"];
  return unsupportedNoticeInfo["default"];
};

export default function Upload() {
  const { locale } = useI18n();
  const navigate = useNavigate();
  const controller = useRef<AbortController | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<UniversalExtractionResult | null>(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState("");
  const [corrections, setCorrections] = useState<Record<string, string>>({});

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
    try { setResult(await api.extractWorkflow(file, controller.current.signal)); }
    catch (e) {
      if ((e as Error).name !== "AbortError") {
        setError(e instanceof ApiError ? e.message : (locale === "hi" ? "सेवा उपलब्ध नहीं है। फिर प्रयास करें।" : "The extraction service is unavailable. Try again."));
      }
    }
    finally { setUploading(false); }
  };
  const confirm = async (confirmed: boolean) => {
    if (!result?.extraction_id || !result.fingerprint || confirming) return;
    setConfirming(true); setError("");
    try {
      const response = await api.confirmWorkflowExtraction(result.extraction_id, result.fingerprint, confirmed, corrections);
      if (!response.supported || !response.notice_id) { setResult(null); setFile(null); setError(locale === "hi" ? "पुष्टि नहीं की गई। सही PDF चुनकर फिर शुरू करें।" : "The extraction was not confirmed. Choose the correct PDF and start again."); return; }
      store.setUploadedNoticeId(response.notice_id); store.setExtractionConfirmed(response.notice_id, true);
      const route = uploadRoute({ ...response, status: response.status, capability: response.capability });
      if (route === "journey") {
        navigate(`/notices/${response.notice_id}/journey?step=questions`, { state: { uploaded: true, startStep: "questions" } });
      } else {
        navigate(`/notices/${response.notice_id}/unsupported`, { state: { uploaded: true } });
      }
    } catch (e) {
      setError(e instanceof ApiError && e.status === 409 ? (locale === "hi" ? "निष्कर्षण सत्र अमान्य या समाप्त हो गया। PDF फिर से अपलोड करें।" : "The extraction session is invalid or expired. Upload the PDF again.") : e instanceof ApiError ? e.message : (locale === "hi" ? "पुष्टि नहीं हो सकी।" : "Confirmation failed."));
    }
    finally { setConfirming(false); }
  };
  const reset = () => { controller.current?.abort(); setFile(null); setResult(null); setError(""); setUploading(false); };
  const refused = result && !result.supported;

  return <WorkflowLayout currentStep={0}>
    <div className="app-page upload-page">
    <GuidedInteraction step={locale === "hi" ? "समझें · चरण 1 / 6" : "Understand · Step 1 of 6"} title={locale === "hi" ? "अपना कर नोटिस अपलोड करें।" : "Upload your tax notice."} instruction={locale === "hi" ? "पहले अपना नोटिस चुनें। इसके बाद Tax Mitra उसे पढ़कर आपके सामने जाँच के लिए रखेगा।" : "Choose your notice first. Tax Mitra will extract it and show you the result to check."} />
    <ol className="upload-process" aria-label={locale === "hi" ? "दस्तावेज़ प्रक्रिया" : "Document process"}>
      <li className={!result ? "is-current" : "is-done"}><span>01</span><strong>{locale === "hi" ? "पढ़ें" : "READ"}</strong></li>
      <li className={result ? "is-current" : ""}><span>02</span><strong>{locale === "hi" ? "जाँचें" : "CHECK"}</strong></li>
      <li><span>03</span><strong>{locale === "hi" ? "पुष्टि" : "CONFIRM"}</strong></li>
      <li><span>04</span><strong>{locale === "hi" ? "मार्गदर्शन" : "GUIDE"}</strong></li>
    </ol>

    {!result && <><label className={`upload-zone${dragging ? " is-dragging" : ""}${uploading ? " is-processing" : ""}`} onDragEnter={dragOver} onDragOver={dragOver} onDragLeave={dragLeave} onDrop={drop}>
      <input type="file" accept="application/pdf,.pdf" onChange={change} disabled={uploading} />
      <span className="upload-icon">{uploading ? "···" : "PDF"}</span><strong>{dragging ? (locale === "hi" ? "PDF यहाँ छोड़ें" : "Release to choose this PDF") : (locale === "hi" ? "PDF यहाँ छोड़ें या चुनें" : "Drop a PDF here or choose a file")}</strong><small>{locale === "hi" ? "अधिकतम 10 MB · टेक्स्ट और स्कैन PDF · स्कैन PDF की पुष्टि आवश्यक होगी" : "Maximum 10 MB · text and scanned PDFs · scanned PDFs require confirmation"}</small>
    </label>
    {file && <div className="upload-receipt">
      <Card className="upload-file"><div><p className="app-section-label">[ DOCUMENT RECEIVED ]</p><strong>{file.name}</strong><small>PDF · {(file.size / 1024 / 1024).toFixed(2)} MB · {locale === "hi" ? "जाँच के लिए तैयार" : "READY TO INSPECT"}</small></div><button onClick={reset} disabled={uploading}>{locale === "hi" ? "हटाएँ" : "REMOVE"}</button></Card>
      {previewUrl && <section className="pdf-preview" aria-label={locale === "hi" ? "चुनी गई PDF का पूर्वावलोकन" : "Selected PDF preview"}><object data={previewUrl} type="application/pdf"><p>{locale === "hi" ? "इस ब्राउज़र में PDF पूर्वावलोकन उपलब्ध नहीं है।" : "PDF preview is unavailable in this browser."}</p></object></section>}
    </div>}
    {uploading && <section className="extraction-status" aria-live="polite"><span className="status-pulse"/><div><p className="app-section-label">[ EXTRACTION IN PROGRESS ]</p><h2>{locale === "hi" ? "आपका नोटिस पढ़ा जा रहा है" : "Reading your notice"}</h2><p>{locale === "hi" ? "दस्तावेज़ मिल गया है। क्रमांकित अनुरोध और आधार निकाले जा रहे हैं।" : "Document received. Numbered requests and their grounding are being extracted."}</p></div></section>}
    <div className="upload-actions">{file && <PrimaryButton onClick={extract} disabled={uploading}>{uploading ? (locale === "hi" ? "पढ़ा जा रहा है…" : "READING PDF…") : (locale === "hi" ? "अनुरोध निकालें" : "EXTRACT REQUESTS")} →</PrimaryButton>}{uploading && <button className="app-back !mt-0" onClick={()=>controller.current?.abort()}>{locale === "hi" ? "रोकें" : "CANCEL"}</button>}<Link className="app-back !mt-0" to="/">← {locale === "hi" ? "होम" : "HOME"}</Link></div></>}

    {result?.supported && <section aria-labelledby="review-title">
      <p className="app-section-label">[ EXTRACTION NEEDS CONFIRMATION ]</p><h2 id="review-title" className="question-title">{locale === "hi" ? "मूल PDF से हर अनुरोध मिलाएँ" : "Match every request to the original PDF"}</h2>

      {(() => {
        const sectionName = result.metadata?.section
          ? `Section ${result.metadata.section}`
          : pick(result.workflow?.title, locale) || (locale === "hi" ? "आयकर नोटिस" : "Income Tax Notice");
        const workflowTitle = pick(result.workflow?.title, locale);
        const workflowDesc = pick((result.workflow as unknown as { description?: Record<string, string> })?.description, locale);
        const pageCount = result.extraction?.page_count ?? result.document?.page_count ?? 1;
        const methodLabel = result.extraction?.method === "ocr"
          ? (locale === "hi" ? "स्कैन PDF" : "Scanned PDF")
          : result.extraction?.method === "mixed"
          ? (locale === "hi" ? "टेक्स्ट + स्कैन PDF" : "Mixed PDF")
          : (locale === "hi" ? "डिजिटल PDF" : "Digital PDF");

        const rawWarnings = [
          ...(result.extraction?.warnings ?? []),
          ...(result.requests ?? []).flatMap(r => r.warnings ?? [])
        ];
        const uniqueWarnings = Array.from(new Set(rawWarnings)).filter(filterInternalMetadata);

        return (
          <>
            <div className="notice-overview-card">
              <div className="notice-badge-group">
                <span className="notice-section-tag">{sectionName}</span>
                {result.metadata?.assessment_year && (
                  <span className="notice-meta-tag">AY {result.metadata.assessment_year}</span>
                )}
                {result.metadata?.response_deadline && (
                  <span className="notice-meta-tag notice-deadline-tag">
                    {locale === "hi" ? "नियत तारीख: " : "Due: "}{result.metadata.response_deadline}
                  </span>
                )}
                {result.metadata?.notice_reference && (
                  <span className="notice-meta-tag">
                    DIN: {result.metadata.notice_reference}
                  </span>
                )}
              </div>
              {workflowTitle && <h3 className="notice-workflow-name">{workflowTitle}</h3>}
              {workflowDesc && <p className="notice-workflow-desc">{workflowDesc}</p>}
              <div className="notice-status-row">
                <span>{locale === "hi" ? "स्थिति: पुष्टि आवश्यक" : "Status: Human verification needed"}</span>
                <span>
                  {pageCount} {locale === "hi" ? "पृष्ठ" : `page${pageCount > 1 ? "s" : ""}`} · {methodLabel}
                </span>
              </div>
            </div>

            {uniqueWarnings.length > 0 && (
              <div className="review-advisory-box">
                <p className="app-section-label">[ {locale === "hi" ? "समीक्षा संबंधी सलाह" : "EXTRACTION ADVISORY"} ]</p>
                <ul className="review-advisory-list">
                  {uniqueWarnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        );
      })()}

      {result.document?.pages?.length ? <details className="original-source page-text-preview">
        <summary>{locale === "hi" ? "निकाला गया पूरा पाठ, पृष्ठ के अनुसार देखें" : "View complete extracted text by page"}<span>{result.document.pages.length} {locale === "hi" ? "पृष्ठ" : "pages"}</span></summary>
        <div className="page-text-list">{result.document.pages.map((page) => <article key={page.page_number} className="page-text-item"><p className="app-section-label">{locale === "hi" ? `पृष्ठ ${page.page_number} · ${page.source}` : `Page ${page.page_number} · ${page.source}`}</p><pre>{page.text || (locale === "hi" ? "इस पृष्ठ से पाठ नहीं मिला।" : "No text was extracted from this page.")}</pre></article>)}</div>
      </details> : null}
      <p className="request-count">{String((result.requests ?? []).length).padStart(2,"0")} {locale === "hi" ? "अनुरोध मिले" : "REQUESTS FOUND"}</p>
      <div className="document-requests">{(result.requests ?? []).map((request,index)=><details className="document-request" key={request.request_id || request.id || index} open={index===0}><summary><span>{String(index+1).padStart(2,"0")}</span><strong>{requestTitle(request, index)}</strong><i>{locale === "hi" ? "खोलें" : "OPEN"}</i></summary><div className="document-request-body"><div className="official-wording"><b>{locale === "hi" ? "अधिकारी के मूल शब्द" : "OFFICIAL REQUEST WORDING"}</b><p className="app-caption">{locale === "hi" ? `स्रोत: पृष्ठ ${request.page_number ?? "—"}` : `Source: page ${request.page_number ?? "—"}`}</p><textarea aria-label={locale === "hi" ? "निकाला गया मूल अनुरोध सुधारें" : "Correct extracted original request"} value={corrections[request.request_id] ?? request.original_text} onChange={(event) => setCorrections((current) => ({ ...current, [request.request_id]: event.target.value }))} rows={4} /></div><div className="scrutiny-explain"><div><b>{locale === "hi" ? "Tax Mitra की आसान भाषा" : "TAX MITRA EXPLANATION"}</b><p>{pick(request.plain_language_explanation,locale)}</p></div><div><b>{locale === "hi" ? "क्यों माँगा गया" : "WHY REQUIRED"}</b><p>{pick(request.why_required,locale) || request.response_section}</p></div></div>{((request.required_evidence?.length ?? 0) > 0)&&<div className="request-evidence"><b>{locale === "hi" ? "संभावित रिकॉर्ड" : "POSSIBLE RECORDS"}</b><ul>{(request.required_evidence ?? []).map((item,i)=><li key={i}>{pick(typeof item === "string" ? { en: item, hi: item } : item,locale)}</li>)}</ul></div>}</div></details>)}</div>
      <div className="human-check"><p className="app-section-label">[ HUMAN CHECK / 02 ]</p><p className="app-body">{locale === "hi" ? "पुष्टि तभी करें जब सूची PDF से पूरी तरह मेल खाती हो। PDF bytes memory में process होते हैं, store या log नहीं होते; session 30 मिनट में समाप्त होता है।" : "Confirm only if this list matches the PDF. PDF bytes are processed in memory and are not stored or logged; the session expires after 30 minutes."}</p></div>
      <div className="confirmation-actions"><PrimaryButton onClick={()=>confirm(true)} disabled={confirming}>{confirming ? (locale === "hi" ? "पुष्टि हो रही है…" : "CONFIRMING…") : (locale === "hi" ? "हाँ, सूची सही है" : "YES, THE LIST MATCHES")} →</PrimaryButton><button onClick={()=>confirm(false)} disabled={confirming}>{locale === "hi" ? "नहीं, फिर से शुरू करें" : "NO, START AGAIN"}</button></div>
    </section>}

    {refused && (() => {
      const isNonTax = result.extraction?.refusal_reason === "not_income_tax_document" || result.classification?.category === "not_income_tax_document";
      const info = getUnsupportedNoticeInfo(result.metadata?.section, result.extraction?.refusal_reason, result.classification?.category);
      return <section className={`app-empty upload-refusal ${isNonTax ? "not-income-tax-refusal" : ""}`} role="alert">
        <p className="app-section-label">{isNonTax ? "[ NOT AN INCOME TAX NOTICE ]" : "[ SAFE STOP ]"}</p>
        <h2 className="question-title">{refusalCopy[result.extraction?.refusal_reason ?? ""]?.[locale] ?? pick(info.title, locale)}</h2>
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
        {(result.extraction?.warnings ?? []).filter(filterInternalMetadata).map((w,i)=><p key={i} className="text-sm text-stone-600 mt-2">{w}</p>)}
        <div className="confirmation-actions">
          {isNonTax ? (
            <PrimaryButton onClick={reset}>{locale === "hi" ? "आधिकारिक नोटिस अपलोड करें" : "Upload official tax notice"} →</PrimaryButton>
          ) : (
            <button onClick={reset}>{locale === "hi" ? "दूसरी PDF चुनें" : "Choose another PDF"}</button>
          )}
          <button onClick={() => navigate("/login")}>{locale === "hi" ? "कार्यशील डेमो इस्तेमाल करें" : "Use a working demo"}</button>
          {info.officialSource && !isNonTax && <a href={info.officialSource.url} target="_blank" rel="noopener noreferrer" className="app-primary">{locale === "hi" ? "आधिकारिक मार्गदर्शन देखें" : "View official guidance"} ↗</a>}
        </div>
      </section>;
    })()}
    {error && <p className="upload-error" role="alert">{error}</p>}
    <div className="notice-boundary"><p className="app-section-label">[ PROCESSING BOUNDARY ]</p><p className="app-body">{locale === "hi" ? "अपलोड की गई फ़ाइल, निकाला गया टेक्स्ट और पुष्टि की गई जानकारी अलग-अलग अवस्थाएं हैं। स्कैन PDF से निकला टेक्स्ट भी आपकी पुष्टि से पहले विश्वसनीय नहीं माना जाता। Tax Mitra कुछ भी जमा नहीं करता।" : "Uploaded, extracted, and confirmed are separate states. Scanned PDF text is also untrusted until you confirm it against the original PDF. Tax Mitra does not submit anything."}</p></div>
    </div>
  </WorkflowLayout>;
}