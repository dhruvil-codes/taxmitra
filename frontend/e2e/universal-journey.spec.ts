import { test, expect, Page, Route } from "@playwright/test";
import axe from "axe-core";

type Capability = "SUPPORTED" | "PARTIAL_SUPPORT" | "EXPLANATION_ONLY" | "SAFE_STOP";
type Scenario = { id: string; workflowId: string; title: string; category: string; capability: Capability; frontendEntry?: "journey" | "scrutiny" | "unsupported"; reason: string; section: string; hindi?: boolean; withEvidence?: boolean };

const request = (id: string, text: string, category = "Information requested") => ({
  id, request_id: id, classification_id: "E2E", original_text: text,
  what_department_is_asking: text,
  plain_language_explanation: { en: `Explain and support: ${text}`, hi: `${text} का विवरण और प्रमाण दें` },
  why_required: { en: "The Department needs this to verify the communication.", hi: "विभाग को संचार की जाँच के लिए यह चाहिए।" },
  required_evidence: [{ en: "Relevant supporting records", hi: "संबंधित सहायक रिकॉर्ड" }], response_section: category,
  citations: [], confidence: 0.96, warnings: [], page_number: 1, source_location: "Page 1 · numbered request", category,
  status: "not_started",
});

const evidence = [{ request_id: "r1", document_id: "bank", document_name: { en: "Bank statement", hi: "बैंक विवरण" }, reason: { en: "Shows the transaction trail requested in the notice.", hi: "नोटिस में मांगी गई लेन-देन श्रृंखला दिखाता है।" }, requirement_level: "required", source: ["page 1"], status: "not_sure" }];

function contractFor(s: Scenario) {
  const requests = s.withEvidence ? [request("r1", "Provide the bank statement for the relevant period", "Bank records"), request("r2", "Explain the source of cash deposits", "Cash deposits")] : s.capability === "EXPLANATION_ONLY" ? [request("r1", "Provide information requested under section 133(6)", "Information request")] : s.capability === "SAFE_STOP" ? [request("r1", "Communication reference and response deadline", "Notice facts")] : [request("r1", s.section === "143(1)(a)" ? "Review the proposed adjustment to reported income" : "Provide the bank statement for the relevant period", s.section)];
  const questions = s.capability === "SUPPORTED" || s.capability === "PARTIAL_SUPPORT" ? [{ id: "position", question_id: "position", text: "Do your records support the position described in the notice?", question: "Do your records support the position described in the notice?", help: "Why we are asking: this answer changes the supported response path.", why_we_are_asking: "This answer changes the supported response path.", options: [{ id: "yes", label: "Yes" }, { id: "not_sure", label: "Not sure" }, { id: "no", label: "No" }], question_type: "single_choice", type: "single_choice", required: true, conditions: [], related_request_ids: ["r1"] }] : [];
  return {
    identity: { workflow_id: s.workflowId, category: s.category, title: { en: s.title, hi: s.hindi ? "धारा 142(1) सूचना" : s.title } },
    capability: s.capability, confidence: s.capability === "SAFE_STOP" ? 0.42 : 0.96, grounding_status: s.capability === "SAFE_STOP" ? "below_floor" : "verified", reason: s.reason,
    notice_facts: { section: s.section, communication_type: s.title, response_deadline: "30 September 2026" }, requests, questions, evidence: s.withEvidence ? evidence : [], safe_stop: { reason: s.reason, facts: { section: s.section, deadline: "30 September 2026" } }, official_portal: { url: "https://www.incometax.gov.in/iec/foportal/", submission_boundary: "Tax Mitra never submits for you." },
  };
}

async function json(route: Route, payload: unknown) { await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(payload) }); }

async function mockScenario(page: Page, s: Scenario, options: { upload?: boolean } = {}) {
  const contract = contractFor(s);
  const notice = { id: s.id, title: s.title, section: s.section, assessment_year: "2025-26", response_deadline: "30 September 2026", issue_date: "01 September 2026", status: "action_required", official_text: `Synthetic ${s.title} communication`, amount: null, days_remaining: 24 };
  await page.route("**/api/**", async (route) => {
    const url = route.request().url();
    const method = route.request().method();
    if (options.upload && method === "POST" && url.endsWith("/api/workflows/extract")) return json(route, { supported: true, status: "needs_confirmation", extraction_id: "extract-e2e", fingerprint: "fingerprint-e2e", metadata: { notice_reference: "E2E-001", section: s.section, assessment_year: "2025-26", response_deadline: "30 September 2026", issue_date: "01 September 2026" }, extraction: { status: "needs_confirmation", confidence: 0.96, warnings: [], refusal_reason: null, method: "text", page_count: 1 }, classification: { workflow_id: s.workflowId, category: s.category, section: s.section, confidence: 0.96, evidence: ["section reference", "department terminology"], capability: s.capability, grounding_status: "verified", reason: s.reason, status: "supported", supported: true, frontend_entry: s.frontendEntry ?? "journey" }, workflow: null, pages: [{ page_number: 1, text: `Synthetic ${s.title}`, source: "text" }], document: { status: "extracted", page_count: 1, sha256: "e2e", pages: [{ page_number: 1, text: `Synthetic ${s.title}`, source: "text" }] }, requests: contract.requests });
    if (options.upload && method === "POST" && url.endsWith("/api/workflows/confirm")) return json(route, { supported: true, status: "confirmed", notice_id: s.id, frontend_entry: s.frontendEntry ?? "journey", capability: s.capability });
    if (method === "POST" && (url.endsWith("/api/scrutiny/resolve-minimum") || url.endsWith("/api/workflow/resolve"))) return json(route, { supported: s.capability !== "SAFE_STOP", draft: s.capability === "SUPPORTED" ? "Synthetic response prepared from your confirmed information." : undefined, checklist: s.withEvidence ? [{ title: { en: "Bank statement", hi: "बैंक विवरण" }, why_needed: { en: "Supports the request.", hi: "अनुरोध का समर्थन करता है।" } }] : [] });
    if (url.endsWith(`/api/notices/${s.id}/workflow`)) return json(route, { notice_id: s.id, classification: { workflow_id: s.workflowId, category: s.category, section: s.section, confidence: contract.confidence, evidence: ["section reference", "document structure"], capability: s.capability, grounding_status: contract.grounding_status, reason: s.reason, status: s.capability === "SAFE_STOP" ? "safe_stop" : "supported", supported: s.capability === "SUPPORTED", frontend_entry: s.frontendEntry ?? "journey" }, workflow: { id: s.workflowId, title: { en: s.title, hi: s.hindi ? "धारा 142(1) सूचना" : s.title }, capability: s.capability }, contract });
    if (url.endsWith(`/api/notices/${s.id}`)) return json(route, notice);
    return route.fallback();
  });
}

async function uploadSynthetic(page: Page) {
  await page.goto("/upload");
  await page.locator('input[type="file"]').setInputFiles({ name: "synthetic-notice.pdf", mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4 synthetic Tax Mitra fixture") });
  await page.getByRole("button", { name: /EXTRACT REQUESTS/i }).click();
  await expect(page.getByText("REQUESTS FOUND")).toBeVisible();
  await page.getByRole("button", { name: /YES, THE LIST MATCHES/i }).click();
}

async function assertAccessible(page: Page) {
  await page.addScriptTag({ content: axe.source });
  const result = await page.evaluate(async () => window.axe.run(document, { rules: { "color-contrast": { enabled: false }, region: { enabled: false } } }));
  expect(result.violations, result.violations.map((violation) => `${violation.id}: ${violation.help}`).join("\n")).toEqual([]);
}

async function uploadRefusal(page: Page, reason: string, method: "ocr" | "none") {
  await page.route("**/api/workflows/extract", async (route) => json(route, { supported: false, status: "safe_stop", metadata: { notice_reference: "E2E-REFUSAL", section: null, assessment_year: "2025-26", response_deadline: null, issue_date: null }, extraction: { status: "safe_stop", confidence: 0.18, warnings: ["No response workflow was opened."], refusal_reason: reason, method, page_count: 1 }, classification: { workflow_id: "unknown_income_tax_communication", category: "unknown", section: null, confidence: 0.18, evidence: ["insufficient extracted text"], capability: "SAFE_STOP", grounding_status: "below_floor", reason: "The communication cannot be classified safely.", status: "safe_stop", supported: false, frontend_entry: "unsupported" }, workflow: null, pages: [] }));
  await page.goto("/upload"); await page.locator('input[type="file"]').setInputFiles({ name: "synthetic-boundary.pdf", mimeType: "application/pdf", buffer: Buffer.from("not a production document") }); await page.getByRole("button", { name: /EXTRACT REQUESTS/i }).click();
}

test.describe("universal Tax Mitra browser journey", () => {
  test("142(1) completes requests, Not sure, evidence, review and portal handoff", async ({ page }) => {
    const s: Scenario = { id: "e2e-142", workflowId: "scrutiny_142_1", title: "Section 142(1) information request", category: "scrutiny", capability: "SUPPORTED", section: "142(1)", frontendEntry: "scrutiny", reason: "Grounded scrutiny requests were identified.", withEvidence: true };
    await mockScenario(page, s, { upload: true });
    const governmentRequests: string[] = [];
    page.on("request", (request) => { if (request.url().includes("incometax.gov.in")) governmentRequests.push(request.url()); });
    await uploadSynthetic(page);
    await expect(page.getByRole("heading", { name: /What the Department is asking/i })).toBeVisible();
    await assertAccessible(page);
    await page.getByRole("article").first().getByText("Original wording and source").click();
    await expect(page.getByText("Page 1 · numbered request").first()).toBeVisible();
    await page.getByRole("button", { name: /Continue/i }).click();
    await expect(page.getByText(/Why we are asking/i)).toBeVisible();
    await page.getByRole("button", { name: "Not sure" }).click();
    await expect(page.getByRole("heading", { name: "What you may need" })).toBeVisible();
    await expect(page.getByText("Bank statement")).toBeVisible();
    await page.getByRole("button", { name: /Continue to review/i }).click();
    await expect(page.getByText("HUMAN REVIEW REQUIRED")).toBeVisible();
    await expect(page.getByText(/Tax Mitra has not submitted anything/i)).toBeVisible();
    const approval = page.getByRole("checkbox");
    await approval.focus();
    await approval.press("Space");
    await expect(approval).toBeChecked();
    await expect(page.getByRole("link", { name: /Open official portal/i })).toHaveAttribute("href", /incometax.gov.in/);
    expect(governmentRequests).toEqual([]);
  });

  test("143(1)(a) uses the universal journey and not scrutiny presentation", async ({ page }) => {
    const s: Scenario = { id: "e2e-143a", workflowId: "income_mismatch_143_1a", title: "Section 143(1)(a) proposed adjustment", category: "processing", capability: "SUPPORTED", section: "143(1)(a)", reason: "A proposed processing adjustment was identified." };
    await mockScenario(page, s, { upload: true }); await uploadSynthetic(page);
    await expect(page).toHaveURL(/\/notices\/e2e-143a\/journey$/);
    await expect(page.getByText("Section 143(1)(a) proposed adjustment")).toBeVisible();
    await expect(page.getByText(/scrutiny requests/i)).toHaveCount(0);
    await page.getByRole("button", { name: /Continue/i }).click();
    await page.getByRole("button", { name: "Not sure" }).click();
    await expect(page.getByText("HUMAN REVIEW REQUIRED")).toBeVisible();
  });

  test("139(9) shows partial support and refuses unsupported legal drafting", async ({ page }) => {
    const s: Scenario = { id: "e2e-1399", workflowId: "defective_return_139_9", title: "Section 139(9) defective return", category: "return_filing", capability: "PARTIAL_SUPPORT", section: "139(9)", reason: "The return is identified as defective; correction guidance is limited to grounded facts." };
    await mockScenario(page, s); await page.goto(`/notices/${s.id}/journey`);
    await expect(page.getByText("Guided with a safe boundary")).toBeVisible();
    await expect(page.getByText(/Review the extracted facts and follow only the next steps supported/i)).toBeVisible();
    await expect(page.getByText(/PREPARED RESPONSE \/ ACTION/i)).toHaveCount(0);
  });

  test("133(6) explanation-only shows meaning, boundary and next step", async ({ page }) => {
    const s: Scenario = { id: "e2e-1336", workflowId: "scrutiny_information_133_6", title: "Section 133(6) information communication", category: "scrutiny", capability: "EXPLANATION_ONLY", section: "133(6)", reason: "Tax Mitra can explain this information communication but cannot safely prepare a response." };
    await mockScenario(page, s); await page.goto(`/notices/${s.id}/journey`);
    await expect(page.getByText("Explanation and next steps")).toBeVisible();
    await expect(page.getByText("What this means for you")).toBeVisible(); await expect(page.getByText("What we found", { exact: true })).toBeVisible(); await expect(page.getByText("What Tax Mitra can help with", { exact: true })).toBeVisible(); await expect(page.getByText("What Tax Mitra cannot safely do", { exact: true })).toBeVisible(); await expect(page.getByText("Next step", { exact: true })).toBeVisible();
    await expect(page.getByText(/prepared response/i)).toHaveCount(0);
  });

  for (const [name, reason] of [["unknown", "The communication could not be classified confidently."], ["ambiguous", "Two workflow categories matched with similar confidence."], ["low-confidence", "The extracted text is below the safe confidence threshold."], ["148", "Reassessment proceedings are legally sensitive and require professional review."]] as const) {
    test(`safe-stops ${name} without an unsafe response`, async ({ page }) => {
      const section = name === "148" ? "148" : "Unknown";
      const s: Scenario = { id: `e2e-${name}`, workflowId: name === "148" ? "reassessment_148" : "unknown_income_tax_communication", title: name === "148" ? "Section 148 reassessment notice" : "Income Tax communication", category: "safe_stop", capability: "SAFE_STOP", section, reason };
      await mockScenario(page, s); await page.goto(`/notices/${s.id}/journey`);
      await expect(page.locator(".capability-safe_stop")).toBeVisible(); await expect(page.getByText(reason, { exact: true })).toBeVisible(); await expect(page.getByText("Next step", { exact: true })).toBeVisible(); await expect(page.getByText(/prepared response/i)).toHaveCount(0);
    });
  }

  test("Hindi switches the shared journey and preserves technical section terminology", async ({ page }) => {
    const s: Scenario = { id: "e2e-hi", workflowId: "scrutiny_142_1", title: "Section 142(1) information request", category: "scrutiny", capability: "SAFE_STOP", section: "142(1)", reason: "यह संचार सुरक्षित रूप से समझाया नहीं जा सका।", hindi: true };
    await mockScenario(page, s); await page.goto(`/notices/${s.id}/journey`);
    await page.getByRole("combobox", { name: "Language" }).selectOption("hi");
    await expect(page.getByText("सुरक्षित रोक", { exact: true })).toBeVisible(); await expect(page.getByRole("heading", { name: /धारा 142\(1\)/ })).toBeVisible(); await expect(page.getByText("Tax Mitra ने क्या पाया", { exact: true })).toBeVisible();
  });

  test("mobile smoke keeps upload and safe boundary usable", async ({ page }) => {
    const s: Scenario = { id: "e2e-mobile", workflowId: "unknown_income_tax_communication", title: "Income Tax communication", category: "safe_stop", capability: "SAFE_STOP", section: "Unknown", reason: "The communication could not be classified confidently." };
    await mockScenario(page, s, { upload: true }); await uploadSynthetic(page); await expect(page.locator(".capability-safe_stop")).toBeVisible(); await expect(page.getByText("Next step", { exact: true })).toBeVisible();
  });

  test("malformed PDF stops at the upload boundary", async ({ page }) => {
    await uploadRefusal(page, "malformed_pdf", "none");
    await expect(page.getByText(/SAFE STOP \/ malformed_pdf/i)).toBeVisible();
    await expect(page.getByText(/WHAT YOU CAN DO NEXT/i)).toBeVisible();
  });

  test("low-confidence OCR stops without opening a workflow", async ({ page }) => {
    await uploadRefusal(page, "low_extraction_confidence", "ocr");
    await expect(page.getByText(/SAFE STOP \/ low_extraction_confidence/i)).toBeVisible();
    await expect(page.getByText(/WHAT YOU CAN DO NEXT/i)).toBeVisible();
    await expect(page.getByText(/PREPARED RESPONSE/i)).toHaveCount(0);
  });

  test("exercises the seeded local frontend/backend integration boundary", async ({ page }) => {
    await page.goto("/notices/N-2026-003/journey");
    await expect(page.getByRole("heading", { name: /142\(1\)/ })).toBeVisible();
    await expect(page.getByText(/What the Department is asking/i)).toBeVisible();
  });
});
