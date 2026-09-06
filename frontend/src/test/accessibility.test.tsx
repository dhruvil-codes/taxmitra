import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";
import { I18nProvider } from "../i18n";
import { NoticeFactsCard } from "../components";

describe("important workflow screen accessibility", () => {
  it("has no axe violations in the notice facts surface", async () => {
    const { container } = render(<MemoryRouter><I18nProvider><NoticeFactsCard notice={{ id: "N", section: "143(1)(a)", category: "income_mismatch_143_1a", supported: true, amount_in_question: 0, title: { en: "Notice", hi: "नोटिस" }, assessment_year: "2024-25", issue_date: "2026-01-01", due_date: "2026-01-31", status: "open", days_remaining: 10 }} /></I18nProvider></MemoryRouter>);
    const results = await axe(container);
    expect(results.violations).toHaveLength(0);
  });
});
