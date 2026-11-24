import { describe, it, expect } from "vitest";
import {
  dateLabel,
  timeLabel,
  dayString,
  apiErrorMessage,
  hasCurrentDates,
  eventSortDate,
} from "./types";
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
      "Event dates → #1 → start date: Enter a valid date.",
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

describe("friendly field validation", () => {
  it.each([
    ["missing", {}, "Please fill in this field."],
    ["string_too_short", { min_length: 1 }, "Please fill in this field."],
    ["string_too_long", { max_length: 250 }, "Use 250 characters or fewer."],
    ["greater_than_equal", { ge: 2000 }, "Enter 2000 or higher."],
    ["less_than_equal", { le: 90 }, "Enter 90 or lower."],
    ["date_from_datetime_parsing", {}, "Enter a valid date (YYYY-MM-DD)."],
    ["time_parsing", {}, "Enter a valid time (HH:MM)."],
    ["int_parsing", {}, "Enter a valid number."],
    ["literal_error", {}, "Choose one of the available options."],
    [
      "json_invalid",
      {},
      "This file isn’t valid JSON. Check its format and try again.",
    ],
    ["unexpected_type", {}, "Check this value and try again."],
  ])(
    "translates %s without exposing technical details",
    (type, ctx, expected) => {
      expect(
        apiErrorMessage([
          {
            type,
            ctx,
            msg: "technical internals",
            loc: ["body", "last_verified"],
            input: "sensitive",
          },
        ]),
      ).toBe(`Last verification date: ${expected}`);
    },
  );
});

describe("today and upcoming events", () => {
  const event = (dates: [string, string][]) =>
    ({
      occurrences: dates.map(([start_date, end_date]) => ({
        start_date,
        end_date,
      })),
    }) as import("./types").Event;
  it("hides ended events but keeps today, future, ongoing and undated events", () => {
    expect(
      hasCurrentDates(event([["2026-11-23", "2026-11-23"]]), "2026-11-24"),
    ).toBe(false);
    for (const dates of [
      [],
      [["2026-11-24", "2026-11-24"]],
      [["2026-11-20", "2026-12-01"]],
      [["2026-12-01", "2026-12-01"]],
    ] as [string, string][][]) {
      expect(hasCurrentDates(event(dates), "2026-11-24")).toBe(true);
    }
  });
  it("uses the next performance even when occurrences arrive out of order", () => {
    const e = event([
      ["2026-12-10", "2026-12-10"],
      ["2026-11-01", "2026-11-01"],
      ["2026-11-24", "2026-11-24"],
    ]);
    expect(eventSortDate(e, "2026-11-24", true)).toBe("2026-11-24");
    expect(eventSortDate(e, "2026-11-24", false)).toBe("2026-11-01");
  });
  it("groups ongoing ranges with today and keeps unknown dates last", () => {
    expect(
      eventSortDate(event([["2026-11-01", "2026-12-01"]]), "2026-11-24", true),
    ).toBe("2026-11-24");
    expect(eventSortDate(event([]), "2026-11-24", true)).toBe("9999");
  });
});
