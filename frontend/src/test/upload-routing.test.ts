import { describe, expect, it } from "vitest";
import { uploadRoute } from "../pages/Upload";

describe("universal upload routing", () => {
  it.each([
    [{ frontend_entry: "journey", supported: true, status: "supported" }, "journey"],
    [{ frontend_entry: "journey", supported: true, status: "supported" }, "journey"],
    [{ frontend_entry: "journey", supported: true, status: "supported", capability: "EXPLANATION_ONLY" }, "journey"],
    [{ frontend_entry: "unsupported", supported: false, status: "safe_stop" }, "safe-stop"],
    [{ frontend_entry: "unsupported", supported: false, status: "safe_stop" }, "safe-stop"],
    [{ frontend_entry: "unsupported", supported: false, status: "safe_stop" }, "safe-stop"],
    [{ frontend_entry: "unsupported", supported: false, status: "safe_stop" }, "safe-stop"],
    [{ frontend_entry: "journey", supported: false, status: "safe_stop" }, "safe-stop"],
  ])("routes %j as %s", (classification, expected) => {
    expect(uploadRoute(classification)).toBe(expected);
  });
});
