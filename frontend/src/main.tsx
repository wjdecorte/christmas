import React, {
  Suspense,
  lazy,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { createRoot } from "react-dom/client";
import {
  Snowflake,
  MapPin,
  Music,
  ArrowUpRight,
  CalendarDays,
  Search,
  SlidersHorizontal,
  Check,
  Clock,
  ArrowLeft,
  ShieldCheck,
  LayoutList,
  Map as MapIcon,
  ExternalLink,
  Sparkles,
  ShoppingBag,
} from "lucide-react";
import "@fontsource/lora/latin-400.css";
import "@fontsource/lora/latin-500.css";
import "@fontsource/source-sans-3/latin-400.css";
import "@fontsource/source-sans-3/latin-600.css";
import "./style.css";
import type { Event, Meta, Venue } from "./types";
import { api, categories, label, dateLabel, timeLabel } from "./types";
const EventMap = lazy(() => import("./Map"));
const Calendar = lazy(() => import("./Calendar"));
const Admin = lazy(() => import("./Admin"));

type Summary = {
  total: number;
  by_city: Record<string, number>;
  by_category: Record<string, number>;
  upcoming: string[];
  concerts: string[];
  weekend: string[];
  free: string[];
  weekend_start: string;
  weekend_end: string;
};
function Badge({ event }: { event: Event }) {
  return (
    <span className={`badge ${event.verified ? "verified" : "unverified"}`}>
      {event.verified ? <Check size={12} /> : <Clock size={12} />}{" "}
      {event.verified ? "Verified" : "Unverified"}
    </span>
  );
}
function EventDate({ event, today }: { event: Event; today: string }) {
  const o =
    event.occurrences.find((o) => o.end_date >= today) || event.occurrences[0];
  return (
    <div className="date-stamp">
      {o ? (
        <>
          <span>{dateLabel(o.start_date, { month: "short" })}</span>
          <strong>{dateLabel(o.start_date, { day: "numeric" })}</strong>
        </>
      ) : (
        <>
          <span>DATE</span>
          <strong className="tba">TBA</strong>
        </>
      )}
    </div>
  );
}
function EventCard({
  event,
  selected,
  today,
  onOpen,
  onSelect,
}: {
  event: Event;
  selected: boolean;
  today: string;
  onOpen: (id: string) => void;
  onSelect: (id: string) => void;
}) {
  const o =
    event.occurrences.find((o) => o.end_date >= today) || event.occurrences[0];
  return (
    <article
      id={"event-" + event.id}
      className={`event-card category-${event.category} ${selected ? "selected" : ""}`}
    >
      <EventDate event={event} today={today} />
      <div className="event-body">
        <div className="event-topline">
          <span className="category">{label(event.category)}</span>
          <Badge event={event} />
          {event.status !== "scheduled" && (
            <span className="badge event-status">{label(event.status)}</span>
          )}
        </div>
        <h3>
          <a
            href={"/events/" + event.id}
            onClick={(e) => {
              e.preventDefault();
              onOpen(event.id);
            }}
          >
            {event.name}
          </a>
        </h3>
        <p className="event-location">
          <MapPin size={14} />
          {event.city}
          {event.venue && ` · ${event.venue.name}`}
        </p>
        <p className="event-time">
          {o
            ? `${dateLabel(o.start_date)}${o.end_date !== o.start_date ? " – " + dateLabel(o.end_date) : ""} · ${timeLabel(o.start_time)}`
            : "Dates to be announced"}
          {event.occurrences.length > 1 &&
            ` · ${event.occurrences.length} performances / dates`}
        </p>
        <div className="event-bottom">
          <span className={event.price_type === "free" ? "free" : "price"}>
            {event.price_type === "free"
              ? "Free admission"
              : event.price_type === "paid"
                ? "Ticketed"
                : "Price TBA"}
          </span>
          {event.venue?.latitude != null ? (
            <button
              className="text-button"
              aria-label={"Show " + event.name + " on map"}
              onClick={() => onSelect(event.id)}
            >
              On the map <ArrowUpRight size={14} />
            </button>
          ) : (
            <span className="location-tba">Location pending</span>
          )}
        </div>
      </div>
    </article>
  );
}
function Detail({ event, onBack }: { event: Event; onBack: () => void }) {
  const v = event.venue;
  const destination =
    v?.latitude != null
      ? `${v.latitude},${v.longitude}`
      : v?.address
        ? `${v.address}, ${v.city}, GA`
        : null;
  return (
    <section className="detail">
      <button className="text-button" onClick={onBack}>
        <ArrowLeft size={16} />
        Back to events
      </button>
      <div className="detail-heading">
        <span className="category">
          {label(event.category)} · {event.city}
        </span>
        <h1>{event.name}</h1>
        <Badge event={event} />
        {event.status !== "scheduled" && (
          <span className="badge event-status">{label(event.status)}</span>
        )}
      </div>
      <div className="detail-columns">
        <div>
          <p className="description">{event.description}</p>
          <h2>When to go</h2>
          {!event.occurrences.length && <p>Dates to be announced.</p>}
          <ul className="schedule">
            {event.occurrences.map((o, i) => (
              <li key={i}>
                <CalendarDays size={18} />
                <div>
                  <strong>
                    {dateLabel(o.start_date, {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                      year: "numeric",
                    })}
                    {o.end_date !== o.start_date
                      ? " – " +
                        dateLabel(o.end_date, {
                          month: "long",
                          day: "numeric",
                          year: "numeric",
                        })
                      : ""}
                  </strong>
                  <p>
                    {timeLabel(o.start_time)}
                    {o.end_time ? " – " + timeLabel(o.end_time) : ""} · Eastern
                    Time
                  </p>
                </div>
              </li>
            ))}
          </ul>
          {event.schedule_notes && (
            <p className="notice">{event.schedule_notes}</p>
          )}
          <h2>Before you head out</h2>
          <p>
            {event.price_type === "free"
              ? "Free admission"
              : event.price_type === "paid"
                ? "Tickets required"
                : "Admission price not yet confirmed"}
            . {event.price_details}
          </p>
          <p className="verification-note">{event.verification_notes}</p>
          <p>
            Last verified:{" "}
            {event.last_verified
              ? dateLabel(event.last_verified, {
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                })
              : "Not yet verified"}
            . Last source check: {event.last_checked || "Not yet checked"}.
          </p>
          {event.source_url ? (
            <a
              className="source-link"
              href={event.source_url}
              target="_blank"
              rel="noreferrer"
            >
              Visit official source <ExternalLink size={16} />
            </a>
          ) : (
            <p>An official source has not yet been attached to this record.</p>
          )}
        </div>
        <aside className="venue-panel">
          <MapPin size={24} />
          <h2>{v?.name || "Venue to be confirmed"}</h2>
          <p>{v?.address || "Street address awaiting confirmation"}</p>
          <p>{event.city}, Georgia</p>
          {destination && (
            <div className="direction-links">
              <a
                href={
                  "https://www.google.com/maps/dir/?api=1&destination=" +
                  encodeURIComponent(destination)
                }
                target="_blank"
                rel="noreferrer"
              >
                Google Maps <ArrowUpRight size={16} />
              </a>
              <a
                href={
                  "https://maps.apple.com/?daddr=" +
                  encodeURIComponent(destination)
                }
                target="_blank"
                rel="noreferrer"
              >
                Apple Maps <ArrowUpRight size={16} />
              </a>
            </div>
          )}
          {v?.coordinate_source && (
            <details>
              <summary>Coordinate source</summary>
              <p>{v.coordinate_source}</p>
            </details>
          )}
        </aside>
      </div>
    </section>
  );
}
function App() {
  const [meta, setMeta] = useState<Meta | null>(null),
    [allEvents, setAllEvents] = useState<Event[]>([]),
    [venues, setVenues] = useState<Venue[]>([]),
    [summary, setSummary] = useState<Summary | null>(null);
  const [year, setYear] = useState(new Date().getFullYear()),
    [query, setQuery] = useState(""),
    [city, setCity] = useState(""),
    [category, setCategory] = useState(""),
    [start, setStart] = useState(""),
    [end, setEnd] = useState(""),
    [verified, setVerified] = useState(false),
    [price, setPrice] = useState(""),
    [sort, setSort] = useState("date"),
    [quick, setQuick] = useState("all");
  const [view, setView] = useState("discover"),
    [selected, setSelected] = useState<string | null>(null),
    [path, setPath] = useState(location.pathname),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [reload, setReload] = useState(0);
  useEffect(() => {
    function pop() {
      setPath(location.pathname);
    }
    window.addEventListener("popstate", pop);
    return () => window.removeEventListener("popstate", pop);
  }, []);
  const refresh = useCallback(() => setReload((n) => n + 1), []);
  useEffect(() => {
    if (view === "admin") return;
    const update = () => {
      if (document.visibilityState === "visible") refresh();
    };
    const timer = setInterval(update, 300000);
    window.addEventListener("focus", update);
    return () => {
      clearInterval(timer);
      window.removeEventListener("focus", update);
    };
  }, [refresh, view]);
  useEffect(() => {
    let live = true;
    setError("");
    Promise.all([
      api<Meta>("/meta"),
      api<Event[]>("/events"),
      api<Venue[]>("/venues"),
    ])
      .then(([m, e, v]) => {
        if (!live) return;
        setMeta(m);
        setAllEvents(e);
        setVenues(v);
        if (reload === 0) setYear(Number(m.today.slice(0, 4)));
      })
      .catch((e) => {
        if (live) setError(e.message);
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [reload]);
  useEffect(() => {
    let live = true;
    api<Summary>("/dashboard?year=" + year)
      .then((d) => {
        if (live) setSummary(d);
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
    };
  }, [year, reload]);
  const today =
    meta?.today ||
    new Date().toLocaleDateString("en-CA", { timeZone: "America/New_York" });
  const open = useCallback((id: string) => {
    history.pushState(null, "", "/events/" + id);
    setPath("/events/" + id);
    window.scrollTo({ top: 0, behavior: "instant" });
  }, []);
  const home = () => {
    history.pushState(null, "", "/");
    setPath("/");
  };
  const select = useCallback((id: string) => {
    setSelected(id);
    document
      .getElementById("event-" + id)
      ?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, []);
  const events = useMemo(() => {
    let e = allEvents.filter(
      (e) =>
        e.season === year &&
        (!city || e.city === city) &&
        (!category || e.category === category) &&
        (!verified || e.verified) &&
        (!price || e.price_type === price) &&
        (!query ||
          `${e.name} ${e.city} ${e.description} ${e.venue?.name || ""}`
            .toLowerCase()
            .includes(query.toLowerCase())) &&
        (!(start || end) ||
          e.occurrences.some(
            (o) =>
              (!start || o.end_date >= start) && (!end || o.start_date <= end),
          )),
    );
    if (quick !== "all" && summary) {
      const ids =
        quick === "concerts"
          ? summary.concerts
          : quick === "weekend"
            ? summary.weekend
            : quick === "free"
              ? summary.free
              : summary.upcoming;
      e = e.filter((e) => ids.includes(e.id));
    }
    return e.sort((a, b) =>
      sort === "name"
        ? a.name.localeCompare(b.name)
        : sort === "city"
          ? a.city.localeCompare(b.city) || a.name.localeCompare(b.name)
          : (
              a.occurrences.find((o) => o.end_date >= (start || today))
                ?.start_date ||
              a.occurrences[0]?.start_date ||
              "9999"
            ).localeCompare(
              b.occurrences.find((o) => o.end_date >= (start || today))
                ?.start_date ||
                b.occurrences[0]?.start_date ||
                "9999",
            ),
    );
  }, [
    allEvents,
    year,
    city,
    category,
    verified,
    price,
    query,
    start,
    end,
    quick,
    summary,
    sort,
    today,
  ]);
  const detailId = path.startsWith("/events/") ? path.split("/")[2] : null;
  const detail = allEvents.find((e) => e.id === detailId);
  function clear() {
    setQuery("");
    setCity("");
    setCategory("");
    setStart("");
    setEnd("");
    setVerified(false);
    setPrice("");
    setQuick("all");
  }
  const tabs = [
    { id: "discover", name: "Discover", icon: LayoutList },
    { id: "map", name: "Map", icon: MapIcon },
    { id: "calendar", name: "Calendar", icon: CalendarDays },
  ];
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to events
      </a>
      <header className="masthead">
        <div className="masthead-inner">
          <a
            className="brand"
            href="/"
            onClick={(e) => {
              e.preventDefault();
              home();
              setView("discover");
            }}
          >
            <img
              className="holiday-mark"
              src="/favicon.svg"
              width="46"
              height="46"
              alt=""
            />
            <span>
              North Georgia<strong>Holiday Events</strong>
            </span>
          </a>
          <span className="header-note">Good company. Close to home.</span>
          <button
            className="admin-link"
            aria-label="Admin"
            onClick={() => {
              home();
              setView("admin");
            }}
          >
            <ShieldCheck size={17} />
            <span>Admin</span>
          </button>
        </div>
      </header>
      <main id="main">
        <div className="page-intro">
          <div className="holiday-flurries" aria-hidden="true">
            <Snowflake />
            <Snowflake />
            <Sparkles />
          </div>
          <div>
            <h1>
              {view === "admin" && !detailId
                ? "A season worth sharing."
                : "Find your holiday tradition."}
            </h1>
            <p>
              Christmas concerts, small-town parades, and a little North Georgia
              magic.
            </p>
          </div>
          <label className="year-select">
            Season
            <select
              value={year}
              onChange={(e) => {
                setYear(Number(e.target.value));
                setSelected(null);
              }}
            >
              {Array.from(
                new Set([
                  ...(meta?.years || []),
                  year,
                  new Date().getFullYear(),
                  new Date().getFullYear() + 1,
                ]),
              )
                .sort()
                .map((y) => (
                  <option key={y}>{y}</option>
                ))}
            </select>
          </label>
        </div>
        {error && (
          <div className="error" role="alert">
            {error} <button onClick={refresh}>Try again</button>
          </div>
        )}
        {loading ? (
          <div className="loading" role="status">
            Gathering the season’s events…
          </div>
        ) : detailId ? (
          detail ? (
            <Detail event={detail} onBack={home} />
          ) : (
            <div className="empty">
              <h2>Event not found</h2>
              <p>It may have been removed from the calendar.</p>
              <button onClick={home}>Back to events</button>
            </div>
          )
        ) : (
          <>
            <nav className="view-nav" aria-label="Event views">
              {tabs.map((t) => {
                const I = t.icon;
                return (
                  <button
                    key={t.id}
                    className={view === t.id ? "active" : ""}
                    aria-current={view === t.id ? "page" : undefined}
                    onClick={() => setView(t.id)}
                  >
                    <I size={17} />
                    {t.name}
                  </button>
                );
              })}
            </nav>
            {view === "admin" ? (
              <Admin
                events={allEvents.filter((e) => e.season === year)}
                venues={venues}
                year={year}
                onChange={refresh}
              />
            ) : (
              <>
                <section className="season-strip" aria-label="Season overview">
                  <div>
                    <span className="stat-number">{summary?.total || 0}</span>
                    <span>ways to celebrate</span>
                  </div>
                  <button
                    className={quick === "concerts" ? "chosen" : ""}
                    onClick={() =>
                      setQuick(quick === "concerts" ? "all" : "concerts")
                    }
                  >
                    <Music size={19} />
                    <span>
                      <strong>
                        {summary?.concerts.length || 0} featured concerts
                      </strong>
                      <small>Make an evening of it</small>
                    </span>
                    <ArrowUpRight size={16} />
                  </button>
                  <button
                    className={quick === "weekend" ? "chosen" : ""}
                    onClick={() =>
                      setQuick(quick === "weekend" ? "all" : "weekend")
                    }
                  >
                    <CalendarDays size={19} />
                    <span>
                      <strong>
                        {summary?.weekend.length || 0} this weekend
                      </strong>
                      <small>
                        {summary
                          ? `${dateLabel(summary.weekend_start)} – ${dateLabel(summary.weekend_end)}`
                          : "Saturday & Sunday"}
                      </small>
                    </span>
                    <ArrowUpRight size={16} />
                  </button>
                  <button
                    className={quick === "free" ? "chosen" : ""}
                    onClick={() => setQuick(quick === "free" ? "all" : "free")}
                  >
                    <Sparkles size={19} />
                    <span>
                      <strong>
                        {summary?.free.length || 0} free activities
                      </strong>
                      <small>A little joy, on the house</small>
                    </span>
                    <ArrowUpRight size={16} />
                  </button>
                </section>
                <section className="filters" aria-label="Filter events">
                  <label className="search-label">
                    <span className="sr-only">Search events</span>
                    <Search size={18} />
                    <input
                      placeholder="Find a little holiday magic…"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </label>
                  <label>
                    <span className="sr-only">City</span>
                    <select
                      value={city}
                      onChange={(e) => setCity(e.target.value)}
                    >
                      <option value="">All towns</option>
                      {meta?.cities.map((c) => (
                        <option key={c}>{c}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span className="sr-only">Category</span>
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                    >
                      <option value="">All kinds of festive</option>
                      {categories.map((c) => (
                        <option key={c} value={c}>
                          {label(c)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <details className="more-filters">
                    <summary>
                      <SlidersHorizontal size={16} />
                      More filters
                    </summary>
                    <div className="filter-popover">
                      <label>
                        From
                        <input
                          type="date"
                          value={start}
                          onChange={(e) => setStart(e.target.value)}
                        />
                      </label>
                      <label>
                        Through
                        <input
                          type="date"
                          value={end}
                          min={start}
                          onChange={(e) => setEnd(e.target.value)}
                        />
                      </label>
                      <label>
                        Admission
                        <select
                          value={price}
                          onChange={(e) => setPrice(e.target.value)}
                        >
                          <option value="">Any price</option>
                          <option value="free">Free</option>
                          <option value="paid">Ticketed</option>
                          <option value="unknown">Price TBA</option>
                        </select>
                      </label>
                      <label className="check">
                        <input
                          type="checkbox"
                          checked={verified}
                          onChange={(e) => setVerified(e.target.checked)}
                        />
                        Verified only
                      </label>
                      <button onClick={clear}>Clear all filters</button>
                    </div>
                  </details>
                </section>
                <div className="results-heading">
                  <div className="button-row">
                    <h2>
                      {quick === "all"
                        ? "Around the neighborhood"
                        : quick === "concerts"
                          ? "Featured Christmas concerts"
                          : quick === "weekend"
                            ? "Happening this weekend"
                            : quick === "free"
                              ? "Free activities"
                              : "Upcoming events"}
                    </h2>
                    <span className="result-count">{events.length} events</span>
                  </div>
                  <label className="sort">
                    Sort by
                    <select
                      value={sort}
                      onChange={(e) => setSort(e.target.value)}
                    >
                      <option value="date">Date</option>
                      <option value="name">Name</option>
                      <option value="city">Town</option>
                    </select>
                  </label>
                </div>
                <div className="quick-filters">
                  <button
                    className={quick === "all" ? "active" : ""}
                    onClick={() => setQuick("all")}
                  >
                    All events
                  </button>
                  <button
                    className={quick === "upcoming" ? "active" : ""}
                    onClick={() => setQuick("upcoming")}
                  >
                    Upcoming
                  </button>
                  {(query ||
                    city ||
                    category ||
                    start ||
                    end ||
                    price ||
                    verified) && <button onClick={clear}>Clear filters</button>}
                </div>
                {start && end && end < start ? (
                  <p className="error" role="alert">
                    Choose an end date on or after the start date.
                  </p>
                ) : view === "calendar" ? (
                  <Calendar
                    key={year}
                    events={events}
                    today={today}
                    year={year}
                    onOpen={open}
                  />
                ) : (
                  <div
                    className={`discovery-layout ${view === "map" ? "map-first" : ""}`}
                  >
                    <div className="event-list">
                      {events.length ? (
                        events.map((e) => (
                          <EventCard
                            key={e.id}
                            event={e}
                            today={today}
                            selected={e.id === selected}
                            onOpen={open}
                            onSelect={select}
                          />
                        ))
                      ) : (
                        <div className="empty">
                          <ShoppingBag size={30} />
                          <h3>No events in this little corner.</h3>
                          <p>Try another town, date, or category.</p>
                          <button onClick={clear}>Show all events</button>
                        </div>
                      )}
                    </div>
                    <EventMap
                      events={events}
                      selected={selected}
                      onSelect={select}
                      onOpen={open}
                    />
                  </div>
                )}
                {summary && (
                  <section className="browse-counts">
                    <div>
                      <h2>Every town has a tradition.</h2>
                      <div className="count-links">
                        {Object.entries(summary.by_city)
                          .sort()
                          .map(([name, count]) => (
                            <button
                              key={name}
                              onClick={() => {
                                setCity(name);
                                setQuick("all");
                              }}
                            >
                              {name}
                              <span>{count}</span>
                            </button>
                          ))}
                      </div>
                    </div>
                    <div>
                      <h2>Find your kind of festive.</h2>
                      <div className="count-links">
                        {Object.entries(summary.by_category)
                          .sort()
                          .map(([name, count]) => (
                            <button
                              key={name}
                              onClick={() => {
                                setCategory(name);
                                setQuick("all");
                              }}
                            >
                              {label(name)}
                              <span>{count}</span>
                            </button>
                          ))}
                      </div>
                    </div>
                  </section>
                )}
              </>
            )}
          </>
        )}
        <footer>
          <img
            className="footer-mark"
            src="/favicon.svg"
            width="34"
            height="34"
            alt=""
          />
          <p>
            Made for a North Georgia Christmas.
            <span>
              Plans can change. Check the official source before heading out.
            </span>
          </p>
          <span className="footer-local">
            <a href="/api/docs">API documentation</a> · All times Eastern
          </span>
        </footer>
      </main>
    </>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Suspense
      fallback={
        <p className="loading" role="status">
          Opening your holiday guide…
        </p>
      }
    >
      <App />
    </Suspense>
  </React.StrictMode>,
);
