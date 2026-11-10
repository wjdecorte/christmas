import { describe, it, expect } from "vitest";
import { dateLabel, timeLabel, dayString } from "./types";
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
