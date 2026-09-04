import { Link } from "react-router-dom";
import { useI18n } from "../i18n";

export default function Start() {
  const { locale } = useI18n();
  const hi = locale === "hi";

  return (
    <div className="app-page start-page">
      <p className="app-eyebrow font-semibold tracking-wider text-slate-500">STARTING POINT</p>
      <h1 className="app-title">{hi ? "आप कैसे शुरू करना चाहते हैं?" : "How do you want to start?"}</h1>
      <p className="app-lead">
        {hi
          ? "सुरक्षित काल्पनिक नोटिस के साथ Tax Mitra आज़माएँ, या अपना आयकर नोटिस लाएँ।"
          : "Try Tax Mitra with a safe fictional notice, or bring your own income-tax notice."}
      </p>

      <div className="start-options" aria-label={hi ? "शुरू करने का तरीका चुनें" : "Choose how to start"}>
        <article className="start-option">
          <p className="start-number">01</p>
          <div>
            <p className="app-section-label font-bold text-blue-600">{hi ? "सुरक्षित डेमो" : "SAFE DEMO"}</p>
            <h2>{hi ? "काल्पनिक नोटिस इस्तेमाल करें" : "Use a synthetic notice"}</h2>
            <p>{hi ? "काल्पनिक डेमो डेटा के साथ Tax Mitra का पूरा अनुभव देखें।" : "Explore the complete Tax Mitra experience with fictional demo data."}</p>
          </div>
          <Link className="start-action" to="/login">{hi ? "काल्पनिक लॉगिन इस्तेमाल करें" : "USE SYNTHETIC LOGIN"} <span aria-hidden="true">→</span></Link>
        </article>

        <div className="start-or" aria-hidden="true">{hi ? "या" : "OR"}</div>

        <article className="start-option is-upload">
          <p className="start-number">02</p>
          <div>
            <p className="app-section-label font-bold text-blue-600">{hi ? "आपका PDF" : "YOUR PDF"}</p>
            <h2>{hi ? "अपना नोटिस इस्तेमाल करें" : "Use your own notice"}</h2>
            <p>{hi ? "आयकर नोटिस है? अपना PDF अपलोड करें और Tax Mitra आपके लिए अनुरोध निकालेगा।" : "Have an income-tax notice? Upload your PDF and Tax Mitra will extract the requests for you."}</p>
          </div>
          <Link className="start-action is-blue" to="/upload">{hi ? "PDF चुनें" : "CHOOSE PDF"} <span aria-hidden="true">→</span></Link>
        </article>
      </div>

      <div className="notice-boundary start-boundary">
        <p className="app-section-label font-bold text-slate-700">{hi ? "महत्वपूर्ण सीमा" : "IMPORTANT BOUNDARY"}</p>
        <p className="app-body">{hi ? "Tax Mitra आपकी ओर से कुछ भी जमा नहीं करता है। आप हर महत्वपूर्ण कार्रवाई की समीक्षा और स्वीकृति करते हैं।" : "Tax Mitra does not submit anything on your behalf. You review and approve every important action."}</p>
      </div>
    </div>
  );
}
