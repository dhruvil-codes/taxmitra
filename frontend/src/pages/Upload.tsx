import { ChangeEvent, DragEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useI18n } from "../i18n";
import { Card } from "../components";

const MAX_SIZE = 10 * 1024 * 1024;

export default function Upload() {
  const { locale } = useI18n();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const choose = (candidate?: File) => {
    if (!candidate) return;
    if (candidate.type !== "application/pdf" && !candidate.name.toLowerCase().endsWith(".pdf")) { setError(locale === "hi" ? "केवल PDF फ़ाइल चुनें।" : "Choose a PDF file only."); return; }
    if (candidate.size > MAX_SIZE) { setError(locale === "hi" ? "PDF 10 MB से छोटी होनी चाहिए।" : "The PDF must be smaller than 10 MB."); return; }
    setError(""); setFile(candidate);
  };
  const drop = (event: DragEvent<HTMLLabelElement>) => { event.preventDefault(); choose(event.dataTransfer.files[0]); };
  const change = (event: ChangeEvent<HTMLInputElement>) => choose(event.target.files?.[0]);
  return <div className="app-page upload-page">
    <p className="app-eyebrow">[ TM / YOUR NOTICE ]</p>
    <h1 className="app-title">{locale === "hi" ? "अपना नोटिस लाएँ" : "Bring your own notice"}</h1>
    <p className="app-lead">{locale === "hi" ? "इस प्रोटोटाइप में आपकी PDF केवल आपके ब्राउज़र में चुनी जाती है। इसे अपलोड या पढ़ा नहीं जाता।" : "In this prototype, your PDF is selected only in your browser. It is not uploaded, stored, or read."}</p>
    <label className="upload-zone" onDragOver={e=>e.preventDefault()} onDrop={drop}>
      <input type="file" accept="application/pdf,.pdf" onChange={change} />
      <span className="upload-icon">PDF</span><strong>{locale === "hi" ? "PDF यहाँ छोड़ें या चुनें" : "Drop a PDF here or choose a file"}</strong><small>{locale === "hi" ? "अधिकतम 10 MB · फ़ाइल आपके डिवाइस पर रहती है" : "Maximum 10 MB · The file stays on your device"}</small>
    </label>
    {error && <p className="upload-error" role="alert">{error}</p>}
    {file && <Card className="upload-file"><div><p className="app-section-label">[ SELECTED LOCALLY ]</p><strong>{file.name}</strong><small>{(file.size / 1024 / 1024).toFixed(2)} MB</small></div><button onClick={()=>setFile(null)}>{locale === "hi" ? "हटाएँ" : "REMOVE"}</button></Card>}
    <div className="notice-boundary"><p className="app-section-label">[ PROCESSING BOUNDARY ]</p><p className="app-body">{locale === "hi" ? "वर्तमान backend में PDF अपलोड या निष्कर्षण endpoint नहीं है। इसलिए Tax Mitra आपकी फ़ाइल से मार्गदर्शन तैयार करने का दावा नहीं करता। काल्पनिक 142(1) डेमो में पूरा अनुभव देखें।" : "The current backend has no PDF upload or extraction endpoint. Tax Mitra therefore does not claim to generate guidance from this file. Use the fictional 142(1) demo to experience the complete journey."}</p></div>
    <div className="upload-actions"><Link className="app-primary" to="/notices/N-2026-003/scrutiny">{locale === "hi" ? "142(1) डेमो देखें" : "OPEN THE 142(1) DEMO"} →</Link><Link className="app-back !mt-0" to="/">← {locale === "hi" ? "होम" : "HOME"}</Link></div>
  </div>;
}
