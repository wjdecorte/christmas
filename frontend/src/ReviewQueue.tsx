import { useCallback, useEffect, useRef, useState } from "react";
import {
  Check,
  Clock,
  ExternalLink,
  Plus,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { api, categories, label, dateLabel, timeLabel } from "./types";
import type { Event, Venue } from "./types";

type Source = {
  id: string;
  name: string;
  url: string;
  kind: string;
  city: string;
  keywords: string;
  link_prefix: string;
  enabled: boolean | number;
  interval_hours: number;
  last_checked: string | null;
  last_error: string;
  last_result: string;
  lease_until: number;
  next_check: number;
};
type Proposal = {
  id: string;
  source_name: string;
  kind: string;
  status: string;
  event_id: string | null;
  before: Partial<Event>;
  proposed: Event;
  venue: Venue | null;
  evidence_url: string;
  evidence_text: string;
  notes: string;
  created_at: string;
};
const newSource = (): Source => ({
  id: "source-" + Date.now(),
  name: "",
  url: "",
  kind: "jsonld",
  city: "",
  keywords: "christmas,holiday,santa,noel,nutcracker",
  link_prefix: "",
  enabled: true,
  interval_hours: 12,
  last_checked: null,
  last_error: "",
  last_result: "",
  lease_until: 0,
  next_check: 0,
});
const fieldNames = [
  "name",
  "city",
  "category",
  "status",
  "occurrences",
  "price_type",
  "price_details",
  "source_url",
  "venue_id",
  "description",
  "schedule_notes",
] as const;
function display(value: unknown) {
  if (value == null || value === "") return "Not provided";
  if (Array.isArray(value))
    return value
      .map(
        (o) =>
          `${dateLabel(o.start_date)}${o.end_date !== o.start_date ? " – " + dateLabel(o.end_date) : ""} · ${timeLabel(o.start_time)}${o.end_time ? " – " + timeLabel(o.end_time) : ""}`,
      )
      .join("\n");
  return String(value);
}
export default function ReviewQueue({
  csrf,
  onChange,
  venues,
  onSessionExpired,
}: {
  csrf: string;
  onChange: () => void;
  venues: Venue[];
  onSessionExpired: () => void;
}) {
  const [sources, setSources] = useState<Source[]>([]),
    [items, setItems] = useState<Proposal[]>([]),
    [filter, setFilter] = useState("pending"),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<Proposal | null>(null),
    [draft, setDraft] = useState<Event | null>(null),
    [venue, setVenue] = useState<Venue | null>(null),
    [note, setNote] = useState(""),
    [source, setSource] = useState<Source | null>(null),
    [adding, setAdding] = useState(false);
  const headers = { "x-csrf-token": csrf };
  const paused = useRef(false);
  useEffect(() => {
    paused.current = !!selected || !!source;
  }, [selected, source]);
  const load = useCallback(async () => {
    const [s, p] = await Promise.all([
      api<Source[]>("/admin/sources"),
      api<Proposal[]>("/admin/review?status=" + filter),
    ]);
    setSources(s);
    setItems(p);
  }, [filter]);
  useEffect(() => {
    let live = true;
    setLoading(true);
    load()
      .catch((e) => {
        if (live) setError(e.message);
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    const timer = setInterval(() => {
      if (!paused.current && document.visibilityState === "visible")
        load().catch(() => {});
    }, 10000);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [load]);
  async function action(fn: () => Promise<unknown>, success: string) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await fn();
      await load();
      setMessage(success);
      onChange();
    } catch (e) {
      setError((e as Error).message);
      if ((e as Error).message === "Sign in to administer events")
        onSessionExpired();
    } finally {
      setBusy(false);
    }
  }
  function open(p: Proposal) {
    setSelected(p);
    setDraft(structuredClone(p.proposed));
    setVenue(p.venue ? structuredClone(p.venue) : null);
    setNote("");
    setError("");
  }
  async function approve() {
    if (!selected || !draft) return;
    await action(async () => {
      await api("/admin/review/" + selected.id + "/approve", {
        method: "POST",
        headers,
        body: JSON.stringify({ event: draft, venue, note }),
      });
      setSelected(null);
      setDraft(null);
    }, "Reviewed event published. Open browser tabs can be refreshed to see it.");
  }
  const changed = selected
    ? fieldNames.filter(
        (k) =>
          JSON.stringify(selected.before?.[k]) !==
          JSON.stringify(selected.proposed[k]),
      )
    : [];
  if (loading && !sources.length)
    return <p role="status">Loading source checks and review items…</p>;
  return (
    <div className="review-workspace">
      <div className="section-heading">
        <div>
          <h3>Check the source. Keep the choice.</h3>
          <p>
            New events and source changes wait here. Nothing is published until
            you approve it.
          </p>
        </div>
        <button
          disabled={busy}
          onClick={() => action(load, "Review queue refreshed")}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="notice">
          {message}
        </p>
      )}
      {selected && draft ? (
        <section className="proposal-editor">
          <div className="section-heading">
            <div>
              <h3>
                {label(selected.kind.replaceAll("_", " "))}: {draft.name}
              </h3>
              <p>
                {selected.source_name} · observed{" "}
                {new Date(selected.created_at).toLocaleString()}
              </p>
            </div>
            <button
              onClick={() => {
                setSelected(null);
                setDraft(null);
              }}
            >
              Close review
            </button>
          </div>
          <a
            className="source-link"
            href={selected.evidence_url}
            target="_blank"
            rel="noreferrer"
          >
            Open source evidence <ExternalLink size={16} />
          </a>
          <p className="notice">
            {selected.kind === "new"
              ? "This is a draft, not a verified event. Confirm the city, schedule, admission and location."
              : selected.kind === "source_unavailable"
                ? "The source page is missing. That does not prove cancellation. Check the organizer before changing event status."
                : selected.kind === "page_changed"
                  ? "Page wording changed. Inspect the source and make any needed event edits below."
                  : "Review the differences against the official source before publishing."}
          </p>
          <div className="comparison-scroll">
            <table className="review-comparison">
              <thead>
                <tr>
                  <th scope="col">Field</th>
                  <th scope="col">Published</th>
                  <th scope="col">Source proposal</th>
                </tr>
              </thead>
              <tbody>
                {(changed.length ? changed : (["name"] as const)).map((k) => (
                  <tr key={k}>
                    <th scope="row">
                      {k === "venue_id"
                        ? "Venue"
                        : label(k.replaceAll("_", " "))}
                    </th>
                    <td>
                      {k === "venue_id"
                        ? (() => {
                            const v = venues.find(
                              (v) => v.id === selected.before?.venue_id,
                            );
                            return v
                              ? `${v.name} · ${v.address}`
                              : "Not provided";
                          })()
                        : display(selected.before?.[k])}
                    </td>
                    <td>
                      {k === "venue_id"
                        ? (() => {
                            const v =
                              selected.venue ||
                              venues.find(
                                (v) => v.id === selected.proposed.venue_id,
                              );
                            return v
                              ? `${v.name} · ${v.address}`
                              : "Not provided";
                          })()
                        : display(selected.proposed[k])}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <details className="evidence">
            <summary>Source excerpts and check notes</summary>
            <p>{selected.notes}</p>
            <p>{selected.evidence_text || "No source text was available."}</p>
          </details>
          {selected.event_id && selected.status === "pending" && (
            <button
              disabled={busy}
              onClick={() =>
                action(async () => {
                  await api("/admin/review/" + selected.id + "/rebase", {
                    method: "POST",
                    headers,
                  });
                  const fresh = await api<Proposal[]>("/admin/review");
                  const p = fresh.find((p) => p.id === selected.id);
                  if (p) open(p);
                }, "Latest published event loaded. Review the differences again before approving.")
              }
            >
              <RefreshCw size={16} />
              Load latest published event
            </button>
          )}
          {selected.status === "pending" && (
            <form
              className="editor"
              onSubmit={(e) => {
                e.preventDefault();
                approve();
              }}
            >
              <h3>Review the event details</h3>
              <div className="form-grid">
                <label>
                  Event name
                  <input
                    required
                    maxLength={250}
                    value={draft.name}
                    onChange={(e) =>
                      setDraft({ ...draft, name: e.target.value })
                    }
                  />
                </label>
                <label>
                  City
                  <input
                    required
                    value={draft.city}
                    onChange={(e) =>
                      setDraft({ ...draft, city: e.target.value })
                    }
                  />
                </label>
                <label>
                  Category
                  <select
                    value={draft.category}
                    onChange={(e) =>
                      setDraft({ ...draft, category: e.target.value })
                    }
                  >
                    {categories.map((c) => (
                      <option value={c} key={c}>
                        {label(c)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Event status
                  <select
                    value={draft.status}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        status: e.target.value as Event["status"],
                      })
                    }
                  >
                    {["scheduled", "cancelled", "postponed"].map((s) => (
                      <option key={s}>{s}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Season
                  <input
                    type="number"
                    required
                    min={2000}
                    max={2200}
                    value={draft.season}
                    onChange={(e) =>
                      setDraft({ ...draft, season: Number(e.target.value) })
                    }
                  />
                </label>
                <label>
                  Admission
                  <select
                    value={draft.price_type}
                    onChange={(e) =>
                      setDraft({ ...draft, price_type: e.target.value })
                    }
                  >
                    {["unknown", "free", "paid"].map((p) => (
                      <option key={p}>{p}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Admission details
                  <input
                    value={draft.price_details}
                    onChange={(e) =>
                      setDraft({ ...draft, price_details: e.target.value })
                    }
                  />
                </label>
                <label>
                  Official source URL
                  <input
                    type="url"
                    required
                    value={draft.source_url}
                    onChange={(e) =>
                      setDraft({ ...draft, source_url: e.target.value })
                    }
                  />
                </label>
              </div>
              <label>
                Description
                <textarea
                  value={draft.description}
                  onChange={(e) =>
                    setDraft({ ...draft, description: e.target.value })
                  }
                />
              </label>
              <fieldset>
                <legend>Dates and times · Eastern Time</legend>
                {draft.occurrences.map((o, i) => (
                  <div className="occurrence-row" key={i}>
                    {(
                      [
                        "start_date",
                        "end_date",
                        "start_time",
                        "end_time",
                      ] as const
                    ).map((k) => (
                      <label key={k}>
                        {label(k.replace("_", " "))}
                        <input
                          type={k.endsWith("date") ? "date" : "time"}
                          required={k.endsWith("date")}
                          value={o[k] || ""}
                          onChange={(e) =>
                            setDraft({
                              ...draft,
                              occurrences: draft.occurrences.map((row, n) =>
                                n === i
                                  ? { ...row, [k]: e.target.value || null }
                                  : row,
                              ),
                            })
                          }
                        />
                      </label>
                    ))}
                    <button
                      type="button"
                      aria-label={"Remove review date " + (i + 1)}
                      onClick={() =>
                        setDraft({
                          ...draft,
                          occurrences: draft.occurrences.filter(
                            (_, n) => n !== i,
                          ),
                        })
                      }
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() =>
                    setDraft({
                      ...draft,
                      occurrences: [
                        ...draft.occurrences,
                        {
                          start_date: `${draft.season}-12-01`,
                          end_date: `${draft.season}-12-01`,
                          start_time: null,
                          end_time: null,
                        },
                      ],
                    })
                  }
                >
                  <Plus size={16} />
                  Add performance
                </button>
              </fieldset>
              <label>
                Schedule notes
                <textarea
                  value={draft.schedule_notes}
                  onChange={(e) =>
                    setDraft({ ...draft, schedule_notes: e.target.value })
                  }
                />
              </label>
              <label>
                Venue
                <select
                  value={draft.venue_id || ""}
                  onChange={(e) => {
                    const value = e.target.value;
                    setDraft({ ...draft, venue_id: value || null });
                    setVenue(
                      value === selected.venue?.id &&
                        !venues.some((v) => v.id === value)
                        ? structuredClone(selected.venue)
                        : null,
                    );
                  }}
                >
                  <option value="">Venue to be confirmed</option>
                  {selected.venue &&
                    !venues.some((v) => v.id === selected.venue?.id) && (
                      <option value={selected.venue.id}>
                        {selected.venue.name} (proposed)
                      </option>
                    )}
                  {venues.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name} · {v.city}
                    </option>
                  ))}
                </select>
              </label>
              {venue && (
                <fieldset>
                  <legend>Proposed venue · not yet mapped</legend>
                  <div className="form-grid">
                    {(["name", "address", "city"] as const).map((k) => (
                      <label key={k}>
                        {label(k)}
                        <input
                          value={venue[k]}
                          required={k !== "address"}
                          onChange={(e) =>
                            setVenue({ ...venue, [k]: e.target.value })
                          }
                        />
                      </label>
                    ))}
                  </div>
                  <p>
                    Coordinates are never guessed. After approval, correct or
                    geocode the saved venue in Venues.
                  </p>
                </fieldset>
              )}
              <label>
                Verification notes
                <textarea
                  value={draft.verification_notes}
                  onChange={(e) =>
                    setDraft({ ...draft, verification_notes: e.target.value })
                  }
                />
              </label>
              <label className="check">
                <input
                  type="checkbox"
                  checked={draft.verified}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      verified: e.target.checked,
                      last_verified: e.target.checked
                        ? new Date().toLocaleDateString("en-CA", {
                            timeZone: "America/New_York",
                          })
                        : null,
                    })
                  }
                />
                I checked the official source and confirm this event
              </label>
              <label>
                Review note (audit history)
                <input
                  value={note}
                  maxLength={2000}
                  onChange={(e) => setNote(e.target.value)}
                />
              </label>
              <div className="button-row">
                <button className="primary" disabled={busy}>
                  <Check size={16} />
                  Approve & publish
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    action(async () => {
                      await api("/admin/review/" + selected.id + "/dismiss", {
                        method: "POST",
                        headers,
                        body: JSON.stringify({ note }),
                      });
                      setSelected(null);
                    }, "Proposal dismissed. Published events were not changed.")
                  }
                >
                  <X size={16} />
                  Dismiss
                </button>
              </div>
            </form>
          )}
        </section>
      ) : (
        <>
          <div className="section-heading">
            <h3>
              Review queue{" "}
              <span className="result-count">
                {items.length} {filter}
              </span>
            </h3>
            <label>
              Show
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              >
                {["pending", "approved", "dismissed", "superseded"].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
          </div>
          {items.length ? (
            <div className="admin-list review-list">
              {items.map((p) => (
                <div key={p.id}>
                  <span>
                    <strong>{p.proposed.name}</strong>
                    <small>
                      {label(p.kind.replaceAll("_", " "))} · {p.source_name} ·{" "}
                      {p.proposed.city}
                    </small>
                  </span>
                  <button onClick={() => open(p)}>
                    {filter === "pending" ? "Review" : "View record"}
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty">
              <Search size={26} />
              <h3>
                {filter === "pending"
                  ? "Nothing waiting for review."
                  : "No items in this history yet."}
              </h3>
              <p>
                Enabled sources are checked on their schedule. You can also
                request a check below.
              </p>
            </div>
          )}
        </>
      )}
      <section className="source-settings">
        <div className="section-heading">
          <div>
            <h3>Approved sources</h3>
            <p>
              Checks respect robots.txt and stay on the approved public HTTPS
              host. Published source URLs on that host are monitored as well.
            </p>
          </div>
          <button
            onClick={() => {
              setAdding(true);
              setSource(newSource());
            }}
          >
            <Plus size={16} />
            Add source
          </button>
        </div>
        {source && (
          <form
            className="editor"
            onSubmit={(e) => {
              e.preventDefault();
              action(async () => {
                await api("/admin/sources" + (adding ? "" : "/" + source.id), {
                  method: adding ? "POST" : "PUT",
                  headers,
                  body: JSON.stringify({
                    ...source,
                    enabled: !!source.enabled,
                  }),
                });
                setSource(null);
              }, "Source saved");
            }}
          >
            <h3>{adding ? "Add approved source" : "Edit source"}</h3>
            <div className="form-grid">
              <label>
                Name
                <input
                  required
                  value={source.name}
                  onChange={(e) =>
                    setSource({ ...source, name: e.target.value })
                  }
                />
              </label>
              <label>
                Default city
                <input
                  required
                  value={source.city}
                  onChange={(e) =>
                    setSource({ ...source, city: e.target.value })
                  }
                />
              </label>
              <label>
                Source URL
                <input
                  required
                  type="url"
                  disabled={!adding}
                  value={source.url}
                  onChange={(e) =>
                    setSource({ ...source, url: e.target.value })
                  }
                />
              </label>
              <label>
                Format
                <select
                  disabled={!adding}
                  value={source.kind}
                  onChange={(e) =>
                    setSource({ ...source, kind: e.target.value })
                  }
                >
                  <option value="jsonld">Event pages / JSON-LD</option>
                  <option value="ical">Calendar feed / iCalendar</option>
                  <option value="page">Monitor one event page</option>
                </select>
              </label>
              <label>
                Event link path prefix (optional)
                <input
                  placeholder="/event/"
                  value={source.link_prefix}
                  onChange={(e) =>
                    setSource({ ...source, link_prefix: e.target.value })
                  }
                />
              </label>
              <label>
                Check every (hours)
                <input
                  type="number"
                  min={6}
                  max={168}
                  value={source.interval_hours}
                  onChange={(e) =>
                    setSource({
                      ...source,
                      interval_hours: Number(e.target.value),
                    })
                  }
                />
              </label>
              <label>
                Holiday keywords (comma separated)
                <input
                  value={source.keywords}
                  onChange={(e) =>
                    setSource({ ...source, keywords: e.target.value })
                  }
                />
              </label>
              <label className="check">
                <input
                  type="checkbox"
                  checked={!!source.enabled}
                  onChange={(e) =>
                    setSource({ ...source, enabled: e.target.checked })
                  }
                />
                Enable scheduled checks
              </label>
            </div>
            <p>
              Confirm this is an official organizer/city source. Add a new
              source rather than changing an existing source's URL or format;
              observation history is preserved.
            </p>
            <div className="button-row">
              <button className="primary" disabled={busy}>
                Save source
              </button>
              <button type="button" onClick={() => setSource(null)}>
                Cancel
              </button>
            </div>
          </form>
        )}
        <div className="admin-list">
          {sources.map((s) => (
            <div className="source-row" key={s.id}>
              <span>
                <strong>
                  {s.name}{" "}
                  <span className="badge verified">
                    {s.enabled ? "Enabled" : "Paused"}
                  </span>
                </strong>
                <small>
                  <a href={s.url} target="_blank" rel="noreferrer">
                    {s.url}
                  </a>
                </small>
                <small>
                  <Clock size={12} /> Every {s.interval_hours} hours ·{" "}
                  {s.last_checked
                    ? "Last check " + new Date(s.last_checked).toLocaleString()
                    : "Not checked yet"}
                </small>
                {s.last_error && <p className="error">{s.last_error}</p>}
                {s.last_result && <p>{s.last_result}</p>}
              </span>
              <div className="button-row">
                <button
                  disabled={
                    busy || !s.enabled || s.lease_until > Date.now() / 1000
                  }
                  onClick={() =>
                    action(
                      () =>
                        api("/admin/sources/" + s.id + "/check", {
                          method: "POST",
                          headers,
                        }),
                      "Source check queued. Results will appear here; publication still requires review.",
                    )
                  }
                >
                  <RefreshCw size={16} />
                  {s.lease_until > Date.now() / 1000
                    ? "Checking…"
                    : "Check now"}
                </button>
                <button
                  onClick={() => {
                    setAdding(false);
                    setSource({ ...s });
                  }}
                >
                  Settings
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
