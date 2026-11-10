import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { Event } from "./types";
import { dayString, dateLabel, timeLabel } from "./types";
export default function Calendar({
  events,
  today,
  year,
  onOpen,
}: {
  events: Event[];
  today: string;
  year: number;
  onOpen: (id: string) => void;
}) {
  const [cursor, setCursor] = useState(
    () =>
      new Date(
        `${year}-${year === Number(today.slice(0, 4)) ? today.slice(5, 7) : "11"}-01T12:00:00`,
      ),
  );
  const [mode, setMode] = useState<"month" | "week">(
    window.innerWidth < 760 ? "week" : "month",
  );
  const start = new Date(cursor);
  if (mode === "month") start.setDate(1);
  start.setDate(start.getDate() - start.getDay());
  const days = Array.from({ length: mode === "month" ? 42 : 7 }, (_, i) => {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    return dayString(d);
  });
  function move(n: number) {
    const d = new Date(cursor);
    if (mode === "month") d.setMonth(d.getMonth() + n);
    else d.setDate(d.getDate() + 7 * n);
    setCursor(d);
  }
  return (
    <section className="calendar">
      <div className="section-heading">
        <div>
          <h2>
            {cursor.toLocaleDateString("en-US", {
              month: "long",
              year: "numeric",
            })}
          </h2>
          <p>All times Eastern. Ranges may have limited operating days.</p>
        </div>
        <div className="button-row">
          <button onClick={() => setMode(mode === "month" ? "week" : "month")}>
            {mode === "month" ? "Week view" : "Month view"}
          </button>
          <button onClick={() => setCursor(new Date(today + "T12:00:00"))}>
            Today
          </button>
          <button aria-label="Previous period" onClick={() => move(-1)}>
            <ChevronLeft size={18} />
          </button>
          <button aria-label="Next period" onClick={() => move(1)}>
            <ChevronRight size={18} />
          </button>
        </div>
      </div>
      <div className="calendar-scroll">
        <div className={`calendar-grid ${mode}`}>
          {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
            <div className="weekday" key={d}>
              {d}
            </div>
          ))}
          {days.map((day) => {
            const dayEvents = events.flatMap((e) =>
              e.occurrences
                .filter((o) => o.start_date <= day && o.end_date >= day)
                .map((o) => ({ e, o })),
            );
            return (
              <div
                key={day}
                className={`calendar-day ${day === today ? "today" : ""} ${day.slice(5, 7) !== dayString(cursor).slice(5, 7) ? "muted-day" : ""}`}
              >
                <time dateTime={day}>
                  {mode === "week" ? dateLabel(day) : Number(day.slice(8))}
                </time>
                {dayEvents.map(({ e, o }, i) => (
                  <button
                    key={e.id + i}
                    className={`calendar-event ${e.verified ? "" : "uncertain"}`}
                    onClick={() => onOpen(e.id)}
                  >
                    {o.start_time && <small>{timeLabel(o.start_time)}</small>}
                    {e.name}
                    {o.start_date !== o.end_date && (
                      <small>Date range · check schedule</small>
                    )}
                    {!e.verified && <small>Unverified</small>}
                  </button>
                ))}
              </div>
            );
          })}
        </div>
      </div>
      {events.some((e) => !e.occurrences.length) && (
        <p className="notice">
          Events with dates to be announced remain in the event list and do not
          appear on the calendar.
        </p>
      )}
    </section>
  );
}
