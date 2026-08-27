import { ChangeEvent, useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useI18n } from "../i18n";
import { Card, PrimaryButton } from "../components";
import { api, ApiError, ExtractionResult, isIntegrationError } from "../lib";

const MAX_PDF_BYTES = 10 * 1024 * 1024;

export default function Landing() {
  const { t } = useI18n();
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [extraction, setExtraction] = useState<ExtractionResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const fileInput = useRef<HTMLInputElement>(null);

  const selectFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setUploadError(null);
    setExtraction(null);
    if (!file) return;
    if (file.size === 0) {
      setUploadError("The selected file is empty.");
      return;
    }
    if (file.size > MAX_PDF_BYTES) {
      setUploadError("PDFs must be 10 MB or smaller.");
      return;
    }
    if (file.type !== "application/pdf") {
      setUploadError("Please select a PDF file.");
      return;
    }
    setSelectedFile(file);
  };

  const upload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      setExtraction(await api.extractPdf(selectedFile));
    } catch (error) {
      if (isIntegrationError(error)) {
        setUploadError("EXTRACTION_UNAVAILABLE: Tax Mitra could not reach the extraction service correctly. Request: POST /api/scrutiny/extract");
      } else if (error instanceof ApiError) {
        // Log detailed error for debugging in development
        if (import.meta.env.DEV) {
          console.error("Extraction API error:", {
            status: error.status,
            detail: error.detail,
            message: error.message,
          });
        }
        setUploadError(error.message);
      } else {
        console.error("Unexpected extraction error:", error);
        setUploadError("The PDF could not be uploaded.");
      }
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    if (searchParams.get("upload") === "1") fileInput.current?.click();
  }, [searchParams]);

  const confirmExtraction = async () => {
    if (!extraction?.extraction_id || !extraction.fingerprint) return;
    setConfirming(true);
    setUploadError(null);
    try {
      const result = await api.confirmExtraction(extraction.extraction_id, extraction.fingerprint);
      navigate(`/notices/${result.notice_id}`);
    } catch (error) {
      setUploadError(error instanceof ApiError ? error.message : "The extracted requests could not be confirmed.");
    } finally {
      setConfirming(false);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setExtraction(null);
    setUploadError(null);
    if (fileInput.current) fileInput.current.value = "";
  };
  const four = [
    ["landing.q1", "landing.q1.sub"],
    ["landing.q2", "landing.q2.sub"],
    ["landing.q3", "landing.q3.sub"],
    ["landing.q4", "landing.q4.sub"],
  ];
  const gptRows = ["landing.gpt.1", "landing.gpt.2", "landing.gpt.3"];
  return (
    <div>
      <section className="px-4 pt-10 pb-8 text-center max-w-2xl mx-auto">
        <p className="text-5xl mb-3" aria-hidden>😰 → 😌</p>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-ink leading-tight">
          {t("landing.hero")}
        </h1>
        <p className="mt-3 text-stone-600 leading-relaxed">{t("landing.sub")}</p>
        <div className="mt-6">
          <PrimaryButton href="/entry">Use Tax Mitra →</PrimaryButton>
        </div>
      </section>

      <section className="px-4 max-w-2xl mx-auto mb-10">
          <Card id="upload">
          <h2 className="font-bold text-lg">Upload a Section 142(1) notice</h2>
          <p className="text-sm text-stone-600 mt-1 leading-relaxed">
            Text-based PDFs only. Your file is sent to the extraction endpoint for review and is not stored.
          </p>
          {!selectedFile ? (
            <label className="mt-4 flex flex-col items-center justify-center border-2 border-dashed border-stone-300 rounded-xl px-4 py-6 text-center cursor-pointer hover:border-saffron">
              <span className="font-semibold text-ink">Choose PDF</span>
              <span className="text-xs text-stone-500 mt-1">Maximum 10 MB</span>
              <input
                ref={fileInput}
                type="file"
                accept="application/pdf,.pdf"
                onChange={selectFile}
                className="sr-only"
              />
            </label>
          ) : (
            <div className="mt-4 rounded-xl border border-india-green/30 bg-india-green-soft p-4">
              <p className="text-xs font-bold uppercase tracking-wide text-india-green">Document received</p>
              <p className="mt-2 break-words text-sm font-semibold text-ink" title={selectedFile.name}>
                {selectedFile.name}
              </p>
              <p className="mt-1 text-xs text-stone-600">
                PDF · {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · Ready to inspect
              </p>
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={removeFile}
                  disabled={uploading}
                  className="text-sm font-semibold text-stone-600 underline disabled:opacity-50"
                >
                  Remove
                </button>
                <button
                  type="button"
                  onClick={upload}
                  disabled={uploading}
                  className="inline-flex items-center justify-center rounded-xl bg-saffron px-5 py-3 text-sm font-bold text-white hover:bg-saffron/90 disabled:opacity-60"
                >
                  {uploading ? "Extracting…" : "Extract requests →"}
                </button>
              </div>
            </div>
          )}
          {uploadError && (
            <div role="alert" className="mt-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">
              {uploadError.startsWith("EXTRACTION_UNAVAILABLE:") ? (
                <>
                  <p className="font-bold">Extraction unavailable</p>
                  <p className="mt-1">Tax Mitra could not reach the extraction service correctly.</p>
                  <p className="mt-1 text-xs">Request: POST /api/scrutiny/extract</p>
                </>
              ) : uploadError}
            </div>
          )}
          {extraction && (
            <div className="mt-4 text-sm bg-stone-50 border border-stone-200 rounded-xl p-4 space-y-2">
              <p className="font-bold">
                {extraction.supported ? "Extraction ready for human confirmation" : "Extraction refused safely"}
              </p>
              <p>Status: {extraction.extraction.status}</p>
              {extraction.metadata?.section && <p>Section: {extraction.metadata.section}</p>}
              {extraction.metadata?.assessment_year && <p>Assessment year: {extraction.metadata.assessment_year}</p>}
              {extraction.supported && <p>Requests found: {extraction.requests?.length ?? 0}</p>}
              <p>Grounding confidence: {extraction.grounding.confidence.toFixed(3)}</p>
              <p>Grounding below floor: {extraction.grounding.below_floor ? "Yes" : "No"}</p>
              {extraction.extraction.refusal_reason && <p>Reason: {extraction.extraction.refusal_reason}</p>}
              {extraction.extraction.warnings.length > 0 && (
                <ul className="list-disc pl-5 text-amber-800">
                  {extraction.extraction.warnings.map((warning) => <li key={warning}>{warning}</li>)}
                </ul>
              )}
              {extraction.supported && extraction.extraction_id && extraction.fingerprint && (
                <button
                  type="button"
                  onClick={confirmExtraction}
                  disabled={confirming}
                  className="mt-3 inline-flex items-center justify-center rounded-xl bg-ink px-5 py-3 text-sm font-bold text-white disabled:opacity-60"
                >
                  {confirming ? "Confirming…" : "Confirm extracted requests →"}
                </button>
              )}
            </div>
          )}
        </Card>
      </section>

      <section className="px-4 max-w-2xl mx-auto" aria-label={t("landing.four.title")}>
        <h2 className="text-center font-bold text-lg mb-4">{t("landing.four.title")}</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {four.map(([q, s]) => (
            <Card key={q} className="flex gap-3 items-start">
              <div className="w-8 h-8 shrink-0 rounded-full bg-saffron-soft text-saffron font-bold flex items-center justify-center">
                {q === "landing.q1" ? "1" : q === "landing.q2" ? "2" : q === "landing.q3" ? "3" : "4"}
              </div>
              <div>
                <h3 className="font-bold text-ink">{t(q)}</h3>
                <p className="text-sm text-stone-600 mt-0.5">{t(s)}</p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className="px-4 max-w-2xl mx-auto mt-10">
        <Card>
          <h2 className="font-bold text-lg mb-3">{t("landing.gpt.title")}</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase text-stone-500">
                  <th className="py-2 pr-2">{t("landing.gpt.col1")}</th>
                  <th className="py-2 pr-2">{t("landing.gpt.col2")}</th>
                  <th className="py-2 text-saffron">{t("landing.gpt.col3")}</th>
                </tr>
              </thead>
              <tbody>
                {gptRows.map((r) => (
                  <tr key={r} className="border-t border-stone-100">
                    <td className="py-2 pr-2 text-stone-600">{t(r)}</td>
                    <td className="py-2 pr-2 text-stone-400">{t(r + "b")}</td>
                    <td className="py-2 font-medium text-ink">{t(r + "c")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-stone-500 italic">
            We use AI to remove the need to know what questions to ask.
          </p>
        </Card>
      </section>

      <section className="px-4 max-w-2xl mx-auto my-10">
        <p className="text-xs text-stone-500 text-center leading-relaxed">{t("landing.trust")}</p>
      </section>
    </div>
  );
}
