import { describe, it, expect } from "vitest";
import { filterInternalMetadata } from "../pages/Upload";

describe("filterInternalMetadata", () => {
  it("filters out request IDs", () => {
    expect(filterInternalMetadata("classification_id: abc123")).toBe(false);
    expect(filterInternalMetadata("request_id: req-123")).toBe(false);
    expect(filterInternalMetadata("extraction_id: ext-456")).toBe(false);
    expect(filterInternalMetadata("fingerprint: fp-789")).toBe(false);
  });

  it("filters out workflow IDs and status", () => {
    expect(filterInternalMetadata("workflow_id: wf-123")).toBe(false);
    expect(filterInternalMetadata("workflow status: active")).toBe(false);
    expect(filterInternalMetadata("grounding_status: verified")).toBe(false);
  });

  it("filters out provider and implementation details", () => {
    expect(filterInternalMetadata("provider: openai")).toBe(false);
    expect(filterInternalMetadata("lexical matching used")).toBe(false);
    expect(filterInternalMetadata("deterministic: false")).toBe(false);
    expect(filterInternalMetadata("backend processing")).toBe(false);
  });

  it("filters out confidence percentages", () => {
    expect(filterInternalMetadata("confidence: 0.95")).toBe(false);
    expect(filterInternalMetadata("confidence: 95%")).toBe(false);
    expect(filterInternalMetadata("REQUEST CONFIDENCE")).toBe(false);
  });

  it("filters out AI/OCR terminology", () => {
    expect(filterInternalMetadata("AI classification is unavailable")).toBe(false);
    expect(filterInternalMetadata("OCR not supported")).toBe(false);
    expect(filterInternalMetadata("ai model: gpt-4")).toBe(false);
    expect(filterInternalMetadata("ocr failure")).toBe(false);
  });

  it("filters out capability enum values", () => {
    expect(filterInternalMetadata("capability: SAFE_STOP")).toBe(false);
    expect(filterInternalMetadata("capability: PARTIAL_SUPPORT")).toBe(false);
    expect(filterInternalMetadata("capability: EXPLANATION_ONLY")).toBe(false);
    expect(filterInternalMetadata("capability: SUPPORTED")).toBe(false);
  });

  it("filters out internal routing messages", () => {
    expect(filterInternalMetadata("deterministic evidence routing was used")).toBe(false);
    expect(filterInternalMetadata("Retrieval and guidance are intentionally deferred")).toBe(false);
    expect(filterInternalMetadata("evidence routing: manual")).toBe(false);
  });

  it("filters out technical implementation details", () => {
    expect(filterInternalMetadata("method: text")).toBe(false);
    expect(filterInternalMetadata("sha256: abc123")).toBe(false);
    expect(filterInternalMetadata("internal error")).toBe(false);
    expect(filterInternalMetadata("implementation detail")).toBe(false);
  });

  it("allows user-facing messages", () => {
    expect(filterInternalMetadata("This PDF is empty")).toBe(true);
    expect(filterInternalMetadata("The text could not be extracted clearly")).toBe(true);
    expect(filterInternalMetadata("No section reference was found")).toBe(true);
    expect(filterInternalMetadata("Please upload a valid PDF")).toBe(true);
  });

  it("handles null and undefined", () => {
    expect(filterInternalMetadata(null)).toBe(false);
    expect(filterInternalMetadata(undefined)).toBe(false);
    expect(filterInternalMetadata("")).toBe(false);
  });

  it("is case-insensitive", () => {
    expect(filterInternalMetadata("CLASSIFICATION_ID: abc")).toBe(false);
    expect(filterInternalMetadata("Workflow_ID: wf-123")).toBe(false);
    expect(filterInternalMetadata("PROVIDER: openai")).toBe(false);
    expect(filterInternalMetadata("Confidence: 0.95")).toBe(false);
  });

  it("filters combined messages with internal terms", () => {
    expect(filterInternalMetadata("Document received. classification_id: abc123")).toBe(false);
    expect(filterInternalMetadata("Processing complete. provider: backend")).toBe(false);
    expect(filterInternalMetadata("Extraction done. confidence: 0.92")).toBe(false);
  });
});
