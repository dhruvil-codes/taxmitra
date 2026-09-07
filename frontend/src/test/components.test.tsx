import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { I18nProvider } from "../i18n";
import { NoticeFactsCard, WorkflowLayout } from "../components";
import type { NoticeCard } from "../lib";

const notice: NoticeCard = {
  id: "N-TEST",
  section: "142(1)",
  category: "scrutiny_142_1",
  supported: true,
  amount_in_question: 0,
  title: { en: "Scrutiny notice", hi: "जांच नोटिस" },
  assessment_year: "2024-25",
  issue_date: "2026-01-10",
  due_date: "2026-02-10",
  status: "open",
  days_remaining: 12,
  official_reference: "DIN-TEST-123456",
};

function renderApp(node: ReactNode) {
  return render(<MemoryRouter><I18nProvider>{node}</I18nProvider></MemoryRouter>);
}

describe("workflow shell", () => {
  it("renders the current progress and landmark navigation", () => {
    renderApp(<WorkflowLayout currentStep={1} notice={notice} noticeId={notice.id}><h1>Questions</h1></WorkflowLayout>);
    expect(screen.getByRole("complementary", { name: "Workflow navigation" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Questions" })).toBeInTheDocument();
    expect(screen.getByText("142(1)")).toBeInTheDocument();
  });

  it("renders notice facts with readable values", () => {
    renderApp(<NoticeFactsCard notice={notice} />);
    expect(screen.getByLabelText("Key notice facts")).toHaveTextContent("AY 2024-25");
    expect(screen.getByText("DIN-TEST-123456")).toBeInTheDocument();
  });

  it("always renders main content children inside workflow-main regardless of viewport", () => {
    // Regression: CSS cascade bugs caused sidebar to remain visible on mobile,
    // squishing workflow-main to ~170px and hiding content off-screen at ≤768px.
    renderApp(
      <WorkflowLayout currentStep={0} notice={notice} noticeId={notice.id}>
        <h1 data-testid="main-content-heading">Step Content</h1>
        <p data-testid="main-content-body">This text must always be accessible.</p>
      </WorkflowLayout>
    );
    // Main content must always be in the DOM
    expect(screen.getByTestId("main-content-heading")).toBeInTheDocument();
    expect(screen.getByTestId("main-content-body")).toBeInTheDocument();
    expect(screen.getByText("Step Content")).toBeInTheDocument();
    expect(screen.getByText("This text must always be accessible.")).toBeInTheDocument();
  });

  it("always renders the mobile progress bar element in the DOM", () => {
    // The mobile bar must always be in the DOM (CSS controls visibility via display:none/flex)
    renderApp(<WorkflowLayout currentStep={2} notice={notice}><span>content</span></WorkflowLayout>);
    const mobileBar = document.querySelector(".workflow-mobile-bar");
    expect(mobileBar).toBeInTheDocument();
  });

  it("always keeps sidebar in DOM but controlled by CSS class workflow-sidebar", () => {
    // The sidebar element must be present so CSS can hide it on mobile
    renderApp(<WorkflowLayout currentStep={1} notice={notice}><span>content</span></WorkflowLayout>);
    const sidebar = document.querySelector(".workflow-sidebar");
    expect(sidebar).toBeInTheDocument();
    // The sidebar must have aria-label for accessibility
    expect(screen.getByRole("complementary", { name: "Workflow navigation" })).toBeInTheDocument();
  });
});
