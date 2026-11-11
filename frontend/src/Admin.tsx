import { useEffect, useState } from "react";
import type { Event, Venue, Occurrence } from "./types";
import { api, categories, label } from "./types";
import ReviewQueue from "./ReviewQueue";
import {
  Plus,
  Trash2,
  Save,
  LogOut,
  Download,
  Upload,
  MapPin,
} from "lucide-react";
const emptyEvent = (year: number): Event => ({
  id: "",
  name: "",
  category: "festival",
  status: "scheduled",
  venue_id: null,
  venue: null,
  city: "",
  description: "",
  price_type: "unknown",
  price_details: "",
  source_url: "",
  verified: false,
  last_verified: null,
  last_checked: null,
  verification_notes: "",
  featured: false,
  season: year,
  schedule_notes: "",
  occurrences: [],
});
const emptyVenue: Venue = {
  id: "",
  name: "",
  address: "",
  city: "",
  latitude: null,
  longitude: null,
  coordinate_source: "",
  geocoded_at: null,
};
export default function Admin({
  events,
  venues,
  year,
  onChange,
}: {
  events: Event[];
  venues: Venue[];
  year: number;
  onChange: () => void;
}) {
  const [csrf, setCsrf] = useState<string | null>(null),
    [checking, setChecking] = useState(true),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  const [tab, setTab] = useState("events"),
    [editing, setEditing] = useState<Event | null>(null),
    [editingVenue, setEditingVenue] = useState<Venue | null>(null),
    [isNew, setIsNew] = useState(false),
    [file, setFile] = useState<{
      name: string;
      format: string;
      content: string;
    } | null>(null);
  useEffect(() => {
    api<{ csrf: string }>("/auth/session")
      .then((d) => setCsrf(d.csrf))
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);
  const headers = { "x-csrf-token": csrf || "" };
  async function action(fn: () => Promise<unknown>, success: string) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await fn();
      setMessage(success);
      onChange();
    } catch (e) {
      setError((e as Error).message);
      if ((e as Error).message === "Sign in to administer events")
        setCsrf(null);
    } finally {
      setBusy(false);
    }
  }
  async function login(e: React.FormEvent) {
    e.preventDefault();
    await action(async () => {
      const d = await api<{ csrf: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ password }),
      });
      setCsrf(d.csrf);
      setPassword("");
    }, "Signed in");
  }
  async function saveEvent(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    await action(async () => {
      await api("/admin/events" + (isNew ? "" : "/" + editing.id), {
        method: isNew ? "POST" : "PUT",
        headers,
        body: JSON.stringify(editing),
      });
      setEditing(null);
    }, "Event saved");
  }
  async function saveVenue(e: React.FormEvent) {
    e.preventDefault();
    if (!editingVenue) return;
    await action(async () => {
      await api("/admin/venues" + (isNew ? "" : "/" + editingVenue.id), {
        method: isNew ? "POST" : "PUT",
        headers,
        body: JSON.stringify(editingVenue),
      });
      setEditingVenue(null);
    }, "Venue saved");
  }
  async function download(format: string) {
    await action(async () => {
      const response = await fetch("/api/admin/export?format=" + format);
      if (!response.ok) throw Error("Export failed. Sign in again.");
      const url = URL.createObjectURL(await response.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = `holiday-events.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    }, "Export downloaded");
  }
  if (checking) return <p role="status">Checking administrator session…</p>;
  const notices = (
    <>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}
    </>
  );
  if (!csrf)
    return (
      <section className="login-panel">
        <h2>Keep the calendar glowing.</h2>
        <p>Sign in to manage events, venues, and verification.</p>
        {notices}
        <form onSubmit={login}>
          <label>
            Administrator password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              required
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button className="primary" disabled={busy}>
            Sign in
          </button>
        </form>
      </section>
    );
  const field = (key: keyof Event, title: string, type = "text") => (
    <label>
      {title}
      <input
        type={type}
        required={["id", "name", "city", "season"].includes(key)}
        disabled={key === "id" && !isNew}
        value={String(editing?.[key] ?? "")}
        onChange={(e) =>
          setEditing((x) =>
            x
              ? {
                  ...x,
                  [key]:
                    key === "season"
                      ? Number(e.target.value)
                      : ["last_verified", "last_checked"].includes(key)
                        ? e.target.value || null
                        : e.target.value,
                }
              : x,
          )
        }
      />
    </label>
  );
  function occurrence(index: number, key: keyof Occurrence, value: string) {
    setEditing((e) =>
      e
        ? {
            ...e,
            occurrences: e.occurrences.map((o, i) =>
              i === index ? { ...o, [key]: value || null } : o,
            ),
          }
        : e,
    );
  }
  return (
    <section className="admin">
      <div className="section-heading">
        <div>
          <h2>Event workshop</h2>
          <p>Changes are saved on this server. All event times are Eastern.</p>
        </div>
        <button
          onClick={() =>
            action(async () => {
              await api("/auth/logout", { method: "POST", headers });
              setCsrf(null);
            }, "Signed out")
          }
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
      {notices}
      <div className="button-row admin-tabs">
        {["events", "review", "venues", "import / export"].map((t) => (
          <button
            key={t}
            className={tab === t ? "active" : ""}
            onClick={() => {
              setTab(t);
              setEditing(null);
              setEditingVenue(null);
            }}
          >
            {label(t)}
          </button>
        ))}
      </div>
      {tab === "review" && (
        <ReviewQueue
          csrf={csrf}
          venues={venues}
          onChange={onChange}
          onSessionExpired={() => setCsrf(null)}
        />
      )}
      {tab === "events" && !editing && (
        <>
          <div className="section-heading">
            <p>
              {events.length} events in the selected season. Change the season
              above to manage another year.
            </p>
            <button
              className="primary"
              onClick={() => {
                setIsNew(true);
                setEditing(emptyEvent(year));
              }}
            >
              <Plus size={16} />
              Add event
            </button>
          </div>
          <div className="admin-list">
            {events.map((e) => (
              <div key={e.id}>
                <span>
                  <strong>{e.name}</strong>
                  <small>
                    {e.city} · {e.verified ? "Verified" : "Unverified"}
                  </small>
                </span>
                <div className="button-row">
                  <button
                    onClick={() => {
                      setIsNew(false);
                      setEditing({ ...e });
                    }}
                  >
                    Edit
                  </button>
                  <button
                    aria-label={"Delete " + e.name}
                    disabled={busy}
                    onClick={() => {
                      if (confirm(`Delete ${e.name}? This cannot be undone.`))
                        action(
                          () =>
                            api("/admin/events/" + e.id, {
                              method: "DELETE",
                              headers,
                            }),
                          "Event deleted",
                        );
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
      {editing && (
        <form className="editor" onSubmit={saveEvent}>
          <h3>{isNew ? "New event" : "Edit " + editing.name}</h3>
          <div className="form-grid">
            {field("name", "Event name")}
            {field("id", "Unique ID (lowercase letters, numbers, hyphens)")}
            {field("city", "City")}
            <label>
              Event status
              <select
                value={editing.status}
                onChange={(e) =>
                  setEditing({
                    ...editing,
                    status: e.target.value as Event["status"],
                  })
                }
              >
                <option value="scheduled">Scheduled</option>
                <option value="cancelled">Cancelled</option>
                <option value="postponed">Postponed</option>
              </select>
            </label>
            {field("season", "Season year", "number")}
            <label>
              Category
              <select
                value={editing.category}
                onChange={(e) =>
                  setEditing({ ...editing, category: e.target.value })
                }
              >
                {categories.map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </label>
            <label>
              Venue
              <select
                value={editing.venue_id || ""}
                onChange={(e) =>
                  setEditing({ ...editing, venue_id: e.target.value || null })
                }
              >
                <option value="">Venue to be confirmed</option>
                {venues.map((v) => (
                  <option value={v.id} key={v.id}>
                    {v.name} · {v.city}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Pricing
              <select
                value={editing.price_type}
                onChange={(e) =>
                  setEditing({ ...editing, price_type: e.target.value })
                }
              >
                {["unknown", "free", "paid"].map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </label>
            {field("price_details", "Price details")}
            {field("source_url", "Official source URL", "url")}
            {field("last_checked", "Last source check", "date")}
            {field("last_verified", "Last verification date", "date")}
          </div>
          <label>
            Description
            <textarea
              value={editing.description}
              onChange={(e) =>
                setEditing({ ...editing, description: e.target.value })
              }
            />
          </label>
          <label>
            Schedule notes
            <textarea
              value={editing.schedule_notes}
              onChange={(e) =>
                setEditing({ ...editing, schedule_notes: e.target.value })
              }
            />
          </label>
          <label>
            Verification notes
            <textarea
              value={editing.verification_notes}
              onChange={(e) =>
                setEditing({ ...editing, verification_notes: e.target.value })
              }
            />
          </label>
          <div className="button-row">
            <label className="check">
              <input
                type="checkbox"
                checked={editing.verified}
                onChange={(e) =>
                  setEditing({ ...editing, verified: e.target.checked })
                }
              />
              Verified against official source
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={editing.featured}
                onChange={(e) =>
                  setEditing({ ...editing, featured: e.target.checked })
                }
              />
              Featured concert
            </label>
          </div>
          <fieldset>
            <legend>Dates and performances</legend>
            <p>
              Add each performance separately, or use a range with schedule
              notes. Leave empty for dates TBA.
            </p>
            {editing.occurrences.map((o, i) => (
              <div className="occurrence-row" key={i}>
                <label>
                  Start date
                  <input
                    type="date"
                    value={o.start_date}
                    required
                    onChange={(e) =>
                      occurrence(i, "start_date", e.target.value)
                    }
                  />
                </label>
                <label>
                  End date
                  <input
                    type="date"
                    value={o.end_date}
                    required
                    onChange={(e) => occurrence(i, "end_date", e.target.value)}
                  />
                </label>
                <label>
                  Start time
                  <input
                    type="time"
                    value={o.start_time || ""}
                    onChange={(e) =>
                      occurrence(i, "start_time", e.target.value)
                    }
                  />
                </label>
                <label>
                  End time
                  <input
                    type="time"
                    value={o.end_time || ""}
                    onChange={(e) => occurrence(i, "end_time", e.target.value)}
                  />
                </label>
                <button
                  type="button"
                  aria-label={"Remove occurrence " + (i + 1)}
                  onClick={() =>
                    setEditing({
                      ...editing,
                      occurrences: editing.occurrences.filter(
                        (_, n) => n !== i,
                      ),
                    })
                  }
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={() =>
                setEditing({
                  ...editing,
                  occurrences: [
                    ...editing.occurrences,
                    {
                      start_date: `${editing.season}-12-01`,
                      end_date: `${editing.season}-12-01`,
                      start_time: null,
                      end_time: null,
                    },
                  ],
                })
              }
            >
              <Plus size={16} />
              Add date / performance
            </button>
          </fieldset>
          <div className="button-row">
            <button className="primary" disabled={busy}>
              <Save size={16} />
              Save event
            </button>
            <button type="button" onClick={() => setEditing(null)}>
              Cancel
            </button>
          </div>
        </form>
      )}
      {tab === "venues" && !editingVenue && (
        <>
          <div className="section-heading">
            <p>
              Geocoding runs only when requested. Saved coordinates are reused
              permanently.
            </p>
            <button
              className="primary"
              onClick={() => {
                setIsNew(true);
                setEditingVenue({ ...emptyVenue });
              }}
            >
              <Plus size={16} />
              Add venue
            </button>
          </div>
          <div className="admin-list">
            {venues.map((v) => (
              <div key={v.id}>
                <span>
                  <strong>{v.name}</strong>
                  <small>
                    {v.city} ·{" "}
                    {v.latitude == null ? "Not mapped" : "Coordinates saved"}
                  </small>
                </span>
                <div className="button-row">
                  <button
                    onClick={() => {
                      setIsNew(false);
                      setEditingVenue({ ...v });
                    }}
                  >
                    Edit location
                  </button>
                  <button
                    aria-label={"Delete " + v.name}
                    disabled={busy}
                    onClick={() => {
                      if (
                        confirm(
                          `Delete ${v.name}? Venues in use cannot be deleted.`,
                        )
                      )
                        action(
                          () =>
                            api("/admin/venues/" + v.id, {
                              method: "DELETE",
                              headers,
                            }),
                          "Venue deleted",
                        );
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
      {editingVenue && (
        <form className="editor" onSubmit={saveVenue}>
          <h3>{isNew ? "New venue" : "Edit venue"}</h3>
          <div className="form-grid">
            {(
              [
                "id",
                "name",
                "city",
                "address",
                "latitude",
                "longitude",
                "coordinate_source",
              ] as const
            ).map((k) => (
              <label key={k}>
                {label(k.replace("_", " "))}
                <input
                  required={["id", "name", "city"].includes(k)}
                  disabled={k === "id" && !isNew}
                  type={
                    ["latitude", "longitude"].includes(k) ? "number" : "text"
                  }
                  step="any"
                  value={editingVenue[k] ?? ""}
                  onChange={(e) =>
                    setEditingVenue({
                      ...editingVenue,
                      [k]: ["latitude", "longitude"].includes(k)
                        ? e.target.value === ""
                          ? null
                          : Number(e.target.value)
                        : e.target.value,
                      ...(["address", "city"].includes(k)
                        ? {
                            latitude: null,
                            longitude: null,
                            coordinate_source: "",
                            geocoded_at: null,
                          }
                        : {}),
                    })
                  }
                />
              </label>
            ))}
          </div>
          <p>
            Use a verified street address. Changing the address clears old
            coordinates. For corrections, enter both coordinates and their
            source.
          </p>
          <div className="button-row">
            <button className="primary" disabled={busy}>
              <Save size={16} />
              Save venue
            </button>
            {!isNew && editingVenue.latitude == null && (
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  action(async () => {
                    await api("/admin/venues/" + editingVenue.id, {
                      method: "PUT",
                      headers,
                      body: JSON.stringify(editingVenue),
                    });
                    const v = await api<Venue>(
                      "/admin/venues/" + editingVenue.id + "/geocode",
                      { method: "POST", headers },
                    );
                    setEditingVenue(v);
                  }, "Coordinates found. Review the location before relying on it.")
                }
              >
                <MapPin size={16} />
                Save & geocode
              </button>
            )}
            <button type="button" onClick={() => setEditingVenue(null)}>
              Cancel
            </button>
          </div>
        </form>
      )}
      {tab === "import / export" && (
        <div className="transfer">
          <h3>Take your calendar with you.</h3>
          <p>
            JSON includes all events and venues. CSV contains one event per row,
            with occurrences and venue data in JSON columns. Exports cover every
            season.
          </p>
          <div className="button-row">
            <button onClick={() => download("json")} disabled={busy}>
              <Download size={16} />
              Export JSON
            </button>
            <button onClick={() => download("csv")} disabled={busy}>
              <Download size={16} />
              Export CSV
            </button>
          </div>
          <h3>Import events</h3>
          <p>
            Imports update matching IDs and add new ones. They never remove
            records. The entire import is validated before any changes are
            saved. Export a backup first.
          </p>
          <label>
            Choose JSON or CSV
            <input
              type="file"
              accept=".json,.csv"
              onChange={async (e) => {
                setError("");
                const f = e.target.files?.[0];
                if (!f) return;
                if (f.size > 4_500_000) {
                  setError("Choose a file smaller than 4.5 MB.");
                  return;
                }
                setFile({
                  name: f.name,
                  format: f.name.toLowerCase().endsWith(".csv")
                    ? "csv"
                    : "json",
                  content: await f.text(),
                });
              }}
            />
          </label>
          {file && (
            <div className="notice">
              <p>
                {file.name} · {file.format.toUpperCase()} ·{" "}
                {new TextEncoder().encode(file.content).length.toLocaleString()}{" "}
                bytes
              </p>
              <details>
                <summary>Review file contents</summary>
                <pre>
                  {file.content.slice(0, 6000)}
                  {file.content.length > 6000 ? "\n…preview truncated" : ""}
                </pre>
              </details>
              <button
                className="primary"
                disabled={busy}
                onClick={() =>
                  action(async () => {
                    const r = await api<{ events: number; venues: number }>(
                      "/admin/import",
                      { method: "POST", headers, body: JSON.stringify(file) },
                    );
                    setFile(null);
                    setMessage(
                      `Imported ${r.events} events and ${r.venues} venues.`,
                    );
                  }, "Import completed")
                }
              >
                <Upload size={16} />
                Apply import
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
