export type Venue = {
  id: string;
  name: string;
  address: string;
  city: string;
  latitude: number | null;
  longitude: number | null;
  coordinate_source: string;
  geocoded_at: string | null;
};
export type Occurrence = {
  start_date: string;
  end_date: string;
  start_time: string | null;
  end_time: string | null;
};
export type Event = {
  id: string;
  name: string;
  category: string;
  status: "scheduled" | "cancelled" | "postponed";
  venue_id: string | null;
  venue: Venue | null;
  city: string;
  description: string;
  price_type: string;
  price_details: string;
  source_url: string;
  verified: boolean;
  last_verified: string | null;
  last_checked: string | null;
  verification_notes: string;
  featured: boolean;
  season: number;
  schedule_notes: string;
  occurrences: Occurrence[];
};
export type Meta = {
  years: number[];
  cities: string[];
  today: string;
  timezone: string;
};
export const categories = [
  "concert",
  "parade",
  "market",
  "lights",
  "tree-lighting",
  "theatre",
  "ice-skating",
  "festival",
];
export const label = (s: string) =>
  s
    .split("-")
    .map((x) => x.charAt(0).toUpperCase() + x.slice(1))
    .join(" ");
export const dateLabel = (
  s: string,
  options: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" },
) => new Date(s + "T12:00:00").toLocaleDateString("en-US", options);
export const timeLabel = (s: string | null) =>
  s
    ? new Date("2000-01-01T" + s).toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
      })
    : "Time TBA";
export const dayString = (date: Date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
const fallbackError = "We couldn’t complete that request. Please try again.";

export function apiErrorMessage(detail: unknown): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (!Array.isArray(detail)) return fallbackError;
  const messages = detail.flatMap((issue: unknown) => {
    if (!issue || typeof issue !== "object") return [];
    const { msg, loc } = issue as { msg?: unknown; loc?: unknown };
    if (typeof msg !== "string" || !msg.trim()) return [];
    const message = msg.replace(/^Value error, /, "");
    const fields = Array.isArray(loc)
      ? loc.filter(
          (part) => part !== "body" && part !== "query" && part !== "path",
        )
      : [];
    const field = fields
      .map((part) =>
        typeof part === "number"
          ? `#${part + 1}`
          : String(part).replaceAll("_", " "),
      )
      .join(" → ");
    return [field ? `${field}: ${message}` : message];
  });
  return [...new Set(messages)].join(". ") || fallbackError;
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const r = await fetch("/api" + path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!r.ok) {
    let msg = fallbackError;
    try {
      const d = await r.json();
      msg = apiErrorMessage(d.detail);
    } catch {}
    throw new Error(msg);
  }
  return r.json();
}
