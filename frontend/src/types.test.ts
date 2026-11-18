import { describe, it, expect } from "vitest";
import { dateLabel, timeLabel, dayString, apiErrorMessage } from "./types";
describe("local holiday dates", () => {
  it("does not shift date-only records to the previous day", () =>
    expect(dateLabel("2026-12-03")).toBe("Dec 3"));
  it("formats unknown and known event times", () => {
    expect(timeLabel(null)).toBe("Time TBA");
    expect(timeLabel("19:30:00")).toBe("7:30 PM");
  });
  it("round trips a local calendar day without UTC conversion", () =>
    expect(dayString(new Date(2027, 0, 2, 12))).toBe("2027-01-02"));
});

describe("API error messages", () => {
  it("shows model validation guidance without the submitted record", () => {
    expect(
      apiErrorMessage([
        {
          loc: ["body"],
          msg: "Value error, Add a verification date.",
          input: { name: "Private event" },
          ctx: { error: {} },
        },
      ]),
    ).toBe("Add a verification date.");
  });
  it("names nested fields and removes duplicate errors", () => {
    const issue = {
      loc: ["body", "occurrences", 0, "start_date"],
      msg: "Enter a valid date",
    };
    expect(apiErrorMessage([issue, issue])).toBe(
      "occurrences → #1 → start date: Enter a valid date",
    );
  });
  it("preserves authentication and other server guidance", () => {
    expect(apiErrorMessage("Sign in again")).toBe("Sign in again");
  });
  it("uses a safe fallback for missing or malformed details", () => {
    for (const detail of [
      null,
      undefined,
      {},
      [],
      [{ input: "private" }],
      "",
    ]) {
      expect(apiErrorMessage(detail)).toBe(
        "We couldn’t complete that request. Please try again.",
      );
    }
  });
});
