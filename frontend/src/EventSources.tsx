import { useEffect, useState } from "react";
import { ExternalLink, Plus, RefreshCw } from "lucide-react";
import { api } from "./types";

type Source = {
  id: string;
  name: string;
  url: string;
  enabled: number | boolean;
  last_checked: string | null;
  last_error: string;
  last_result: string;
  lease_until: number;
  interval_hours: number;
};
export default function EventSources({
  eventId,
  csrf,
}: {
  eventId: string;
  csrf: string;
}) {
  const [sources, setSources] = useState<Source[]>([]);
  const [url, setUrl] = useState(""),
    [name, setName] = useState("");
  const [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true);
  const path = `/admin/events/${encodeURIComponent(eventId)}/sources`;
  const headers = { "x-csrf-token": csrf };
  async function load() {
    setSources(await api<Source[]>(path));
  }
  useEffect(() => {
    let active = true;
    const refresh = () =>
      api<Source[]>(path)
        .then((s) => {
          if (active) {
            setSources(s);
            setLoading(false);
          }
        })
        .catch((e) => {
          if (active) {
            setError(e.message);
            setLoading(false);
          }
        });
    void refresh();
    const timer = window.setInterval(refresh, 10000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [path]);
  async function action(fn: () => Promise<unknown>, success: string) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await fn();
      await load();
      setMessage(success);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <fieldset className="event-sources">
      <legend>Additional sources</legend>
      <p>
        Attach public HTTPS event pages to check for more details. Checks use
        the saved event, keep its original source, and send changes to Admin →
        Review. Save your event edits before checking sources.
      </p>
      <p>
        Structured event data can suggest dates, prices, descriptions and
        venues. Other pages provide excerpts for manual review. Login-only or
        blocked pages cannot be scraped.
      </p>
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
      <div className="form-grid">
        <label>
          Source label (optional)
          <input
            value={name}
            maxLength={200}
            onChange={(e) => setName(e.target.value)}
            placeholder="Organizer event page"
          />
        </label>
        <label>
          Additional event URL
          <input
            type="text"
            inputMode="url"
            value={url}
            maxLength={2000}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://organizer.example/event"
          />
        </label>
      </div>
      <button
        type="button"
        disabled={busy || !url.trim()}
        onClick={() =>
          void action(async () => {
            await api(path, {
              method: "POST",
              headers,
              body: JSON.stringify({ url, name }),
            });
            setUrl("");
            setName("");
          }, "Source saved. Its first check is queued; review any suggested changes before publishing.")
        }
      >
        <Plus size={16} /> Add URL & queue check
      </button>
      {loading ? (
        <p role="status">Loading additional sources…</p>
      ) : sources.length === 0 ? (
        <p>No additional sources yet.</p>
      ) : (
        <ul className="event-source-list">
          {sources.map((source) => (
            <li key={source.id}>
              <a href={source.url} target="_blank" rel="noopener noreferrer">
                {source.name} <ExternalLink size={14} />
              </a>
              <p className="source-url">{source.url}</p>
              <small>
                {source.enabled
                  ? `Scheduled every ${source.interval_hours} hours`
                  : "Paused"}{" "}
                ·{" "}
                {source.last_checked
                  ? `Last checked ${new Date(source.last_checked).toLocaleString()}`
                  : "Not checked yet"}
                {source.lease_until > Date.now() / 1000 ? " · Checking…" : ""}
              </small>
              {source.last_error && (
                <p className="error">{source.last_error}</p>
              )}
              {source.last_result && <p>{source.last_result}</p>}
              <div className="button-row">
                <button
                  type="button"
                  disabled={
                    busy ||
                    !source.enabled ||
                    source.lease_until > Date.now() / 1000
                  }
                  onClick={() =>
                    void action(
                      () =>
                        api(`/admin/sources/${source.id}/check`, {
                          method: "POST",
                          headers,
                        }),
                      "Check queued. Results will appear here and in Review.",
                    )
                  }
                >
                  <RefreshCw size={14} /> Check now
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    void action(
                      () =>
                        api(
                          `/admin/events/${encodeURIComponent(eventId)}/sources/${source.id}`,
                          {
                            method: "PATCH",
                            headers,
                            body: JSON.stringify({ enabled: !source.enabled }),
                          },
                        ),
                      source.enabled
                        ? "Source paused."
                        : "Source enabled; check queued.",
                    )
                  }
                >
                  {source.enabled ? "Pause checks" : "Enable checks"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </fieldset>
  );
}
