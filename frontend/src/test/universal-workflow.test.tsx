import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { ContractEvidence, ContractExplanation, ContractQuestion, ContractRequests, CapabilityBadge, CapabilityBoundary } from "../components/UniversalWorkflow";
import type { EvidenceRecommendation, NoticeCard, ScrutinyRequest, WorkflowCapability } from "../lib";

const request = (category: string, text: string): ScrutinyRequest => ({
  id: category, request_id: category, classification_id: category, original_text: text,
  plain_language_explanation: { en: `Plain explanation for ${category}` }, why_required: { en: "Needed to address the notice request." },
  required_evidence: [], response_section: category, citations: [], confidence: 0.94, warnings: [], page_number: 2, source_location: "page 2", category,
});
const evidence: EvidenceRecommendation[] = [{ request_id: "r1", document_id: "r1:records", document_name: { en: "Supporting records" }, reason: { en: "Supports the request." }, requirement_level: "required", source: [], status: "not_sure" }];
const notice: NoticeCard = { id: "n1", title: { en: "Section 142(1) information request" }, section: "142(1)", category: "scrutiny", supported: true, amount_in_question: 0, issue_date: "2026-08-20", due_date: "2026-09-18", assessment_year: "2025-26", days_remaining: 12, official_text: "Original notice wording: provide the requested records and explanations.", status: "needs_action" };

function renderWithRouter(node: React.ReactNode) { return render(<MemoryRouter>{node}</MemoryRouter>); }

describe("universal workflow contract renderer", () => {
  it.each<[WorkflowCapability, string]>([["SUPPORTED", "Guided workflow"], ["PARTIAL_SUPPORT", "Guided with a safe boundary"], ["EXPLANATION_ONLY", "Explanation and next steps"], ["SAFE_STOP", "Safe stop"]])("renders capability %s honestly", (capability, label) => {
    renderWithRouter(<CapabilityBadge capability={capability} locale="en" />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("renders any number of extracted requests with wording and provenance", () => {
    renderWithRouter(<ContractRequests requests={[request("computation", "1. Provide computation"), request("bank", "2. Provide bank statements"), request("cash", "3. Explain cash deposits")]} locale="en" />);
    expect(screen.getByText("What the Department is asking")).toBeInTheDocument();
    expect(screen.getByText("03", { exact: true })).toBeInTheDocument();
    expect(screen.getAllByText(/Plain explanation for/).length).toBe(3);
  });

  it.each<[WorkflowCapability, string]>([["SUPPORTED", "142(1) information request"], ["SUPPORTED", "143(1)(a) proposed adjustment"], ["EXPLANATION_ONLY", "133(6) information communication"], ["SAFE_STOP", "Section 148 proceeding"]])("renders a structured explanation for %s", (capability, title) => {
    renderWithRouter(<ContractExplanation capability={capability} title={title} reason="The communication was classified from its grounded facts." notice={notice} requests={[request("balance-sheet", "Provide the balance sheet")]} nextSteps={["Review the deadline", "Use the official portal where required"]} originalText={notice.official_text} locale="en" />);
    expect(screen.getByText("What this notice means")).toBeInTheDocument();
    expect(screen.getByText(title)).toBeInTheDocument();
    expect(screen.getByText("What the Department wants")).toBeInTheDocument();
    expect(screen.getByText("Deadline")).toBeInTheDocument();
    expect(screen.getByText("Each request")).toBeInTheDocument();
    expect(screen.getByText("Plain explanation for balance-sheet")).toBeInTheDocument();
    expect(screen.getByText("What happens next")).toBeInTheDocument();
    expect(screen.getByText("What Tax Mitra can help with")).toBeInTheDocument();
  });

  it("keeps original wording behind a secondary action", () => {
    renderWithRouter(<ContractExplanation capability="SUPPORTED" title="142(1) information request" reason="Grounded classification" notice={notice} requests={[request("r1", "Provide records")] } nextSteps={[]} originalText={notice.official_text} locale="en" />);
    expect(screen.getByText(notice.official_text ?? "")).not.toBeVisible();
    fireEvent.click(screen.getByText("View original notice wording"));
    expect(screen.getByText(notice.official_text ?? "")).toBeVisible();
  });

  it("renders single choice options and preserves Not sure", () => {
    const onChange = vi.fn();
    renderWithRouter(<ContractQuestion question={{ id: "source", text: "What is the source?", help: "Why", options: [{ id: "business", label: "Business sales" }, { id: "unsure", label: "Not sure" }], question_type: "single_choice" }} locale="en" value={undefined} onChange={onChange} onContinue={vi.fn()} />);
    fireEvent.click(screen.getByLabelText("Not sure"));
    expect(onChange).toHaveBeenCalledWith("unsure");
  });

  it("supports multi-select without collapsing answers", () => {
    const onChange = vi.fn();
    renderWithRouter(<ContractQuestion question={{ id: "sources", text: "Which sources apply?", help: "Why", options: [{ id: "sales", label: "Sales" }, { id: "loan", label: "Loan" }], question_type: "multi_choice" }} locale="en" value={[]} onChange={onChange} onContinue={vi.fn()} />);
    fireEvent.click(screen.getByLabelText("Sales"));
    fireEvent.click(screen.getByLabelText("Loan"));
    expect(onChange).toHaveBeenNthCalledWith(1, ["sales"]);
    expect(onChange).toHaveBeenNthCalledWith(2, ["loan"]);
  });

  it("opens a text field for Something else", () => {
    const onChange = vi.fn();
    const { rerender } = renderWithRouter(<ContractQuestion question={{ id: "source", text: "What is the source?", help: "Why", options: [{ id: "something_else", label: "Something else" }], question_type: "choice_with_other" }} locale="en" value={undefined} onChange={onChange} onContinue={vi.fn()} />);
    fireEvent.click(screen.getByLabelText("Something else"));
    expect(onChange).toHaveBeenCalledWith({ choice: "something_else", other: "" });
    rerender(<ContractQuestion question={{ id: "source", text: "What is the source?", help: "Why", options: [{ id: "something_else", label: "Something else" }], question_type: "choice_with_other" }} locale="en" value={{ choice: "something_else", other: "" }} onChange={onChange} onContinue={vi.fn()} />);
    expect(screen.getByLabelText("Something else", { selector: "textarea" })).toBeInTheDocument();
  });

  it("keeps genuinely explanatory questions as free text", () => {
    const onContinue = vi.fn();
    renderWithRouter(<ContractQuestion question={{ id: "explain", text: "Explain the transaction", help: "Why", options: [], question_type: "text" }} locale="en" value="" onChange={vi.fn()} onContinue={onContinue} />);
    fireEvent.change(screen.getByLabelText("Explain the transaction"), { target: { value: "My explanation" } });
    fireEvent.click(screen.getByText("Continue"));
    expect(onContinue).toHaveBeenCalled();
  });

  it("renders evidence from mappings without asking redundant document questions", () => {
    renderWithRouter(<ContractEvidence evidence={evidence} locale="en" />);
    expect(screen.getByText("Supporting records")).toBeInTheDocument();
    expect(screen.getByText(/Required by the notice/)).toBeInTheDocument();
  });

  it.each<WorkflowCapability>(["EXPLANATION_ONLY", "SAFE_STOP"]) ("renders a reusable boundary for %s", (capability) => {
    renderWithRouter(<CapabilityBoundary capability={capability} reason="The classification is not safe for automated response preparation." nextSteps={["Review the deadline", "Consult a qualified professional"]} locale="en" />);
    expect(screen.getByText("The classification is not safe for automated response preparation.")).toBeInTheDocument();
    expect(screen.getByText("Consult a qualified professional")).toBeInTheDocument();
  });
});
