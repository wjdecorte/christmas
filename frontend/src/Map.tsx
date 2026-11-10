import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet.markercluster";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { renderToStaticMarkup } from "react-dom/server";
import {
  Music,
  ShoppingBag,
  Sparkles,
  Flag,
  TreePine,
  Drama,
  MapPin,
  Snowflake,
} from "lucide-react";
import type { Event } from "./types";
import { dateLabel, label } from "./types";
const symbols: { [key: string]: typeof Music } = {
  concert: Music,
  market: ShoppingBag,
  lights: Sparkles,
  parade: Flag,
  "tree-lighting": TreePine,
  theatre: Drama,
  "ice-skating": Snowflake,
  festival: MapPin,
};
export default function EventMap({
  events,
  selected,
  onSelect,
  onOpen,
}: {
  events: Event[];
  selected: string | null;
  onSelect: (id: string) => void;
  onOpen: (id: string) => void;
}) {
  const element = useRef<HTMLDivElement>(null),
    map = useRef<L.Map | null>(null),
    markers = useRef(new Map<string, L.Marker>()),
    cluster = useRef<L.MarkerClusterGroup | null>(null);
  const [tileError, setTileError] = useState(false);
  useEffect(() => {
    if (!element.current) return;
    const m = L.map(element.current, { scrollWheelZoom: false }).setView(
      [34.15, -84.39],
      9,
    ); // Viewport center, never an event coordinate.
    map.current = m;
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    })
      .on("tileerror", () => setTileError(true))
      .addTo(m);
    const observer = new ResizeObserver(() => m.invalidateSize());
    observer.observe(element.current);
    return () => {
      observer.disconnect();
      m.remove();
      map.current = null;
    };
  }, []);
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    const group = L.markerClusterGroup({
      showCoverageOnHover: false,
      maxClusterRadius: 40,
    });
    cluster.current = group;
    markers.current.clear();
    const points: L.LatLngTuple[] = [];
    events.forEach((event) => {
      const v = event.venue;
      if (v?.latitude == null || v.longitude == null) return;
      const Icon = symbols[event.category] || MapPin;
      const marker = L.marker([v.latitude, v.longitude], {
        title: event.name,
        icon: L.divIcon({
          className: `event-pin pin-${event.category}`,
          html: renderToStaticMarkup(<Icon size={17} aria-hidden="true" />),
          iconSize: [34, 34],
          iconAnchor: [17, 17],
        }),
      });
      const box = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = event.name;
      box.append(title);
      const detail = document.createElement("p");
      detail.textContent = `${event.occurrences[0] ? dateLabel(event.occurrences[0].start_date) : "Dates TBA"} · ${v.name}`;
      box.append(detail);
      const button = document.createElement("button");
      button.textContent = "View event details";
      button.addEventListener("click", () => onOpen(event.id));
      box.append(button);
      marker.bindPopup(box).on("click", () => onSelect(event.id));
      group.addLayer(marker);
      markers.current.set(event.id, marker);
      points.push([v.latitude, v.longitude]);
    });
    m.addLayer(group);
    if (points.length)
      m.fitBounds(L.latLngBounds(points), { padding: [35, 35], maxZoom: 12 });
    return () => {
      m.removeLayer(group);
    };
  }, [events, onSelect, onOpen]);
  useEffect(() => {
    if (!selected) return;
    const marker = markers.current.get(selected);
    if (marker && map.current) {
      cluster.current?.zoomToShowLayer(marker, () => marker.openPopup());
    }
  }, [selected, events]);
  const count = events.filter((e) => e.venue?.latitude != null).length;
  return (
    <section className="map-section" aria-label="Event map">
      <div className="map-heading">
        <div>
          <h2>A little closer to home</h2>
          <p>
            {count} mapped events · {events.length - count} awaiting a location
          </p>
        </div>
        <MapPin size={20} />
      </div>
      <div ref={element} className="map-canvas" />
      {tileError && (
        <p className="map-note">
          Map tiles are unavailable. Event listings and addresses still work.
          Check your internet connection.
        </p>
      )}
      <div className="map-legend">
        {["concert", "parade", "market", "lights"].map((c) => {
          const I = symbols[c];
          return (
            <span key={c}>
              <I size={14} />
              {label(c)}
            </span>
          );
        })}
      </div>
      <p className="map-note">
        Only sourced coordinates appear on the map. Select a pin to find its
        event.
      </p>
    </section>
  );
}
