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

  const significantTransactionsQuestion = {
    id: "significant_transaction_explanation",
    text: "How would you explain the significant credits and debits?",
    help: "The explanation determines which transaction records may help and what needs review.",
    options: [
      { id: "business_transactions", label: "Business transactions recorded in my books" },
      { id: "loan_or_borrowing", label: "Loan received or repaid" },
      { id: "personal_or_family_transfer", label: "Personal or family transfer" },
      { id: "something_else", label: "Something else" },
    ],
    question_type: "choice_with_other" as const,
  };

  it("renders the 142(1) credits/debits question as backend choices, not a free-text box", () => {
    const onChange = vi.fn();
    const onContinue = vi.fn();
    const { rerender } = renderWithRouter(<ContractQuestion question={significantTransactionsQuestion} locale="en" value={undefined} onChange={onChange} onContinue={onContinue} />);
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    for (const option of significantTransactionsQuestion.options) {
      expect(screen.getByLabelText(option.label)).toHaveAttribute("type", "radio");
    }
    fireEvent.click(screen.getByLabelText("Loan received or repaid"));
    expect(onChange).toHaveBeenCalledWith("loan_or_borrowing");
    rerender(<ContractQuestion question={significantTransactionsQuestion} locale="en" value="loan_or_borrowing" onChange={onChange} onContinue={onContinue} />);
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    const continueButton = screen.getByRole("button", { name: "Continue" });
    expect(continueButton).toBeEnabled();
    fireEvent.click(continueButton);
    expect(onContinue).toHaveBeenCalled();
  });

  it("reveals the free-text field only after Something else is chosen for the 142(1) question", () => {
    const onChange = vi.fn();
    const onContinue = vi.fn();
    const { rerender } = renderWithRouter(<ContractQuestion question={significantTransactionsQuestion} locale="en" value={undefined} onChange={onChange} onContinue={onContinue} />);
    fireEvent.click(screen.getByLabelText("Something else"));
    expect(onChange).toHaveBeenCalledWith({ choice: "something_else", other: "" });
    rerender(<ContractQuestion question={significantTransactionsQuestion} locale="en" value={{ choice: "something_else", other: "" }} onChange={onChange} onContinue={onContinue} />);
    const otherField = screen.getByLabelText("Something else", { selector: "textarea" });
    expect(screen.getByRole("button", { name: "Continue" })).toBeDisabled();
    fireEvent.change(otherField, { target: { value: "Agricultural income receipts" } });
    expect(onChange).toHaveBeenLastCalledWith({ choice: "something_else", other: "Agricultural income receipts" });
    rerender(<ContractQuestion question={significantTransactionsQuestion} locale="en" value={{ choice: "something_else", other: "Agricultural income receipts" }} onChange={onChange} onContinue={onContinue} />);
    const continueButton = screen.getByRole("button", { name: "Continue" });
    expect(continueButton).toBeEnabled();
    fireEvent.click(continueButton);
    expect(onContinue).toHaveBeenCalled();
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

  it("renders compact one-line collapsed requests that expand into explanation, why required, and original wording", () => {
    renderWithRouter(
      <ContractRequests
        requests={[
          {
            ...request("req_bank_statements", "Please furnish certified true copies of all bank accounts maintained during the relevant previous year 2023-24 along with narration of credit entries exceeding Rs. 50,000."),
            what_department_is_asking: "Bank account statements and narrations",
            response_section: "Bank statements and deposit explanations",
            source_location: "Page 2 · ¶ 4",
          },
        ]}
        locale="en"
      />
    );
    // Summary is concise, not the huge raw paragraph
    expect(screen.getByText("Bank account statements and narrations")).toBeInTheDocument();
    expect(screen.getAllByText("Page 2 · ¶ 4").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Expand ↓")).toBeInTheDocument();
    expect(screen.getByText("What the Department wants")).toBeInTheDocument();
    expect(screen.getByText("Requested information / Why required")).toBeInTheDocument();
    expect(screen.getByText("Original notice wording")).toBeInTheDocument();
    expect(screen.getByText(/certified true copies of all bank accounts/)).toBeInTheDocument();
  });

  it("does not expose internal grounding or classifier diagnostics", () => {
    renderWithRouter(<ContractRequests requests={[request("r-debug", "Provide the notice records")]} locale="en" />);
    expect(screen.queryByText(/REQUEST CONFIDENCE|DETERMINISTIC RULE|classification_id|NOT_PROVIDED|SAFE_STOP/)).not.toBeInTheDocument();
  });

  it("renders Answer the Notice question with department requisition details and supporting notes", () => {
    const onChange = vi.fn();
    const onContinue = vi.fn();
    const deptQuestion = {
      id: "req_1",
      text: "What is your position regarding Requisition 1 (Books of Accounts)?",
      help: "Requirement: Needed to substantiate entries.",
      section: "answer_the_notice" as const,
      department_request: {
        request_id: "req_1",
        title: "Books of Accounts",
        original_text: "Produce books of accounts including ledger, cash book, and journal.",
        plain_meaning: "The department requires certified books of account for the financial year.",
        why_required: "To verify total income returned.",
        page: 2,
        amount: 250000,
      },
      question_type: "choice_with_other" as const,
      options: [
        { id: "provide", label: "Will provide requested document in full" },
        { id: "partial", label: "Only partial records available" },
        { id: "not_applicable", label: "Not applicable" },
        { id: "explain", label: "Clarification only" },
      ],
    };

    const { rerender } = renderWithRouter(
      <ContractQuestion
        question={deptQuestion}
        locale="en"
        value={undefined}
        onChange={onChange}
        onContinue={onContinue}
      />
    );

    // Verify requisition card content
    expect(screen.getByText("DEPARTMENT REQUISITION · PAGE 2")).toBeInTheDocument();
    expect(screen.getByText("₹2,50,000")).toBeInTheDocument();
    expect(screen.getByText('"Produce books of accounts including ledger, cash book, and journal."')).toBeInTheDocument();
    expect(screen.getByText("The department requires certified books of account for the financial year.")).toBeInTheDocument();
    expect(screen.getByText(/To verify total income returned/)).toBeInTheDocument();

    // Verify taxpayer options
    expect(screen.getByLabelText("Will provide requested document in full")).toBeInTheDocument();
    expect(screen.getByLabelText("Only partial records available")).toBeInTheDocument();

    // Selecting an option triggers onChange with choice and current details
    fireEvent.click(screen.getByLabelText("Will provide requested document in full"));
    expect(onChange).toHaveBeenCalledWith({ choice: "provide", details: "" });

    // Rerender with chosen option and type details
    rerender(
      <ContractQuestion
        question={deptQuestion}
        locale="en"
        value={{ choice: "provide", details: "" }}
        onChange={onChange}
        onContinue={onContinue}
      />
    );

    const detailsInput = screen.getByLabelText("Supporting details");
    expect(detailsInput).toBeInTheDocument();
    fireEvent.change(detailsInput, { target: { value: "Ledger Folio 42, audited copy attached" } });
    expect(onChange).toHaveBeenCalledWith({
      choice: "provide",
      details: "Ledger Folio 42, audited copy attached",
      other: "Ledger Folio 42, audited copy attached",
    });
  });
});

