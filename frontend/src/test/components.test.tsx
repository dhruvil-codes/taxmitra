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
});
