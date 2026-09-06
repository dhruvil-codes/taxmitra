import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { ContractEvidence, ContractRequests, CapabilityBadge, CapabilityBoundary } from "../components/UniversalWorkflow";
import type { EvidenceRecommendation, ScrutinyRequest, WorkflowCapability } from "../lib";

const request = (category: string, text: string): ScrutinyRequest => ({
  id: category, request_id: category, classification_id: category, original_text: text,
  plain_language_explanation: { en: `Plain explanation for ${category}` }, why_required: { en: "Needed to address the notice request." },
  required_evidence: [], response_section: category, citations: [], confidence: 0.94, warnings: [], page_number: 2, source_location: "page 2", category,
});
const evidence: EvidenceRecommendation[] = [{ request_id: "r1", document_id: "r1:records", document_name: { en: "Supporting records" }, reason: { en: "Supports the request." }, requirement_level: "required", source: [], status: "not_sure" }];

function renderWithRouter(node: React.ReactNode) { return render(<MemoryRouter>{node}</MemoryRouter>); }

describe("universal workflow contract renderer", () => {
  it.each<[WorkflowCapability, string]>([["SUPPORTED", "Guided workflow"], ["PARTIAL_SUPPORT", "Guided with a safe boundary"], ["EXPLANATION_ONLY", "Explanation and next steps"], ["SAFE_STOP", "Safe stop"]])("renders capability %s honestly", (capability, label) => {
    renderWithRouter(<CapabilityBadge capability={capability} locale="en" />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("renders any number of extracted requests with wording, provenance and confidence", () => {
    renderWithRouter(<ContractRequests requests={[request("computation", "1. Provide computation"), request("bank", "2. Provide bank statements"), request("cash", "3. Explain cash deposits")]} locale="en" />);
    expect(screen.getByText("What the Department is asking")).toBeInTheDocument();
    expect(screen.getByText("03", { exact: true })).toBeInTheDocument();
    expect(screen.getAllByText(/94% confidence/).length).toBe(3);
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
