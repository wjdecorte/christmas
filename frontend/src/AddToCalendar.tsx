import { useState } from "react";
import { CalendarPlus } from "lucide-react";
import { api } from "./types";

type Links = { google: string; outlook: string; office: string };
export default function AddToCalendar({
  eventId,
  occurrence,
  timeUnknown,
}: {
  eventId: string;
  occurrence: number;
  timeUnknown: boolean;
}) {
  const [links, setLinks] = useState<Links | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  async function show() {
    setOpen(!open);
    if (links || open) return;
    setBusy(true);
    setError("");
    try {
      const entries = await api<Links[]>(
        `/events/${encodeURIComponent(eventId)}/calendar`,
      );
      if (!entries[occurrence])
        throw new Error(
          "This event date is no longer available. Refresh the page and try again.",
        );
      setLinks(entries[occurrence]);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Calendar options couldn’t load. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="add-calendar">
      <button type="button" onClick={show} aria-expanded={open}>
        <CalendarPlus size={16} aria-hidden="true" /> Add to calendar
      </button>
      {open && (
        <div className="calendar-options">
          <p>
            {timeUnknown
              ? "Time TBA: saved as an all-day reminder. "
              : "Times are Eastern. "}
            Review the details before saving. This copy won’t update
            automatically.
          </p>
          {busy && <p role="status">Loading calendar options…</p>}
          {error && <p role="alert">{error}</p>}
          <div className="button-row">
            {links && (
              <>
                <a
                  href={links.google}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Google Calendar
                </a>
                <a
                  href={links.outlook}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Outlook.com
                </a>
                <a
                  href={links.office}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Microsoft 365
                </a>
              </>
            )}
            <a
              href={`/api/events/${encodeURIComponent(eventId)}/calendar.ics?occurrence=${occurrence}`}
              download
            >
              Apple / other calendars (.ics)
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
