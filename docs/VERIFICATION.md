# Local verification — November 10, 2026

## Automated checks

- `uv run pytest -q`: 16 passing backend tests, covering read-only public access, protected writes/exports, CSRF and origin enforcement, session logout, login throttling, event/venue CRUD, future seasons, recurring-date and interval filtering, unknown coordinates, invalid data, import rollback, CSV/JSON round trips, one-time seeding, geocoding caching, duplicate/malformed CSV rejection, body size limits, backup/restore and session revocation.
- `npm --prefix frontend test`: 3 passing date/time tests.
- `npm --prefix frontend run build`: TypeScript and production Vite build pass.
- npm dependency installation/audit: zero reported advisories after upgrading Vitest.
- One non-failing development warning: the installed Starlette version deprecates its TestClient httpx adapter in favor of httpx2. Production HTTP checks were also run separately against Python 3.12 inside Docker.

## Docker verification

- Native and Synology-compatible `linux/amd64` images built successfully. Final amd64 image tagged `north-georgia-holiday-events:local` in local Docker.
- The checked-in Compose configuration validated and started with an isolated temporary data directory and temporary random administrator credential.
- Container reports healthy with a read-only filesystem, non-root UID 1000, dropped capabilities, persistent SQLite bind mount and loopback-only test port.
- Documented in-container SQLite backup, stopped-app restore via a one-off Compose container, and restart passed.
- Recreating the app retained SQLite data without reseeding.
- Final HTTP smoke verifies 43 records, 10 confirmed and 16 with sourced coordinates, detail page fallback routing, locally served Swagger assets, typed OpenAPI event responses, admin cookie login and protected JSON export.

## Browser verification

Production served by Docker, at desktop 1440×1000 and mobile 390×844:

- Map/list selection → marker popup → detail page → return.
- Search narrows results, verified filter returns ten records, clearing filters restores all events.
- Monthly/weekly calendar switching, mobile week default and contained month scrolling.
- Admin sign-in, create/save an event in disposable data, venue editor access, import/export interface and sign-out.
- Local Swagger docs render without external script/CDN dependencies.
- Mobile document width does not exceed viewport width.
- Browser error log showed no JavaScript errors during inspected workflows.
- Independent Impeccable review: **Ship** at the reviewed frontend scope; no material design findings. Detector's sole underline warning is a false positive: active navigation explicitly has zero corner radius.

Screenshots are local QA artifacts under `.impeccable/review/` (ignored by source control). Temporary preview containers are stopped after verification. No NAS connection or deployment was attempted.

## Remaining operational work

Set real administrator credentials, data-directory permissions and LAN binding on the NAS, then deploy using README instructions. Thirty-three supplied events remain unverified and 27 have no sourced coordinates; these remain visible with explicit labels/location-pending states. Some organizer prices and hours are unknown. Geocoding address results may require manual precision corrections. Event/source updates remain manual, as requested.
