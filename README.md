# North Georgia Holiday Events

A self-hosted Christmas outings guide for North Georgia. React/TypeScript/Vite/Tailwind, FastAPI, SQLite, Leaflet with clustered OpenStreetMap markers. One container serves the built frontend and REST API; no account, paid API, or cloud database is required.

## What is included

- Discover events by town, category, date, admission, verification and search; sort by date, name or town.
- Upcoming events, featured concerts, this weekend, free activities, and counts by town/category.
- Synchronized listings and map, event detail URLs, Google/Apple directions.
- Monthly and weekly calendars. Mobile defaults to week; month can scroll within the calendar.
- One administrator: event/venue CRUD, coordinate correction and requested geocoding, verification, all-season JSON/CSV import/export.
- 43 supplied seed events for the 2026 season, including dated runs and attractions with dates TBA. Confirmed facts and source links are embedded in the dataset; incomplete entries are explicitly unverified.
- Versioned SQL migrations, automated tests, health checks and SQLite backup/restore commands.

## Synology Container Manager deployment

Uses the same pattern as Picker: **GitHub Actions → GHCR image → NAS pulls with Compose**. Do not copy the source tree or build on the NAS. The workflow tests the backend/frontend before publishing amd64 and arm64 images; the DS1821+ selects amd64.

Copy only `deploy/synology/compose.yaml` and `deploy/synology/.env.example` to the NAS project folder, configure `.env` and data permissions, then:

```sh
docker compose pull
docker compose up -d --wait
```

Open `http://YOUR_NAS_IP:8090`. Full instructions, registry login, persistent-data permissions, and updates are in [Synology deployment](deploy/synology/README.md).

Default image: `ghcr.io/wjdecorte/christmas:latest`; set `CHRISTMAS_IMAGE` to a commit tag or immutable digest for a pinned deployment. Root and NAS Compose files both pull images. GitHub Actions uses its built-in token; private image pulls need the NAS's GHCR login. Check the [workflow](https://github.com/wjdecorte/christmas/actions/workflows/image.yaml) for successful first publication before pulling. Application data stays on the NAS.

### Optional local source build

For development or an offline transfer, explicitly use the build override:

```sh
docker compose -f compose.yaml -f compose.build.yaml up -d --build
```

Set `DATA_DIR` to a writable local directory when using this on the Mac. To build the Synology architecture and transfer an image without GHCR:

```sh
docker buildx build --platform linux/amd64 --load -t north-georgia-holiday-events:local .
docker save -o holiday-events-amd64.tar north-georgia-holiday-events:local
```

Load the archive on the NAS and set `CHRISTMAS_IMAGE=north-georgia-holiday-events:local`, then run `docker compose up -d --pull never`. This is an optional fallback; registry pulls are the default.

## Local development

Requires Python 3.12+, uv, Node 24+ and npm. Dependencies are locked in `uv.lock` and `frontend/package-lock.json`.

```sh
uv sync
cd frontend
npm ci
cd ..
cp .env.example .env
# Edit .env and set ADMIN_PASSWORD. The backend reads this file with --env-file.
uv run uvicorn app.main:app --app-dir backend --env-file .env --host 127.0.0.1 --port 8091
```

In a second terminal:

```sh
cd frontend
npm run dev
```

Open Vite's printed local URL. It proxies `/api` to 8091. For production-style local preview, first `npm --prefix frontend run build`, then run Uvicorn on your desired local port; it serves `frontend/dist`. `/api/docs` uses locally packaged Swagger assets after a frontend build. The Vite dev server's CSP behavior differs from production because it serves HMR scripts; verify production via the backend or Docker.

Local SQLite defaults to `data/events.sqlite3`. `DATABASE_PATH` overrides it. `.env` is read by Uvicorn only when `--env-file` is supplied; Compose uses it for configuration automatically.

```sh
uv run pytest -q
npm --prefix frontend test
npm --prefix frontend run build
```

Backend tests cover authorization/CSRF/origin checks, login limits, CRUD, future years, date overlap/recurrence, atomic rollback, JSON/CSV round trips, geocoding cache, request size limits and one-time seeding. Frontend unit tests cover date/time interpretation. Run browser checks against a production build for map/list and responsive interaction verification.

## Administrator workflow

- Choose a season at the top, then **Admin**. Add an event with its season year, category and venue; IDs are stable lowercase letters/numbers/hyphens.
- Add each actual performance as a separate date/time row. For a multiweek attraction, a range is supported; describe closures and daily hours in schedule notes. Date ranges are clearly labeled in the calendar and do not prove daily operation. Unknown dates use no occurrence rows and remain in the list, outside date-filtered/calendar results.
- Dates and times are local `America/New_York` wall times. Start/end dates support overnight events and runs into the following year. Season year controls the season selector independently of occurrence year; January 2027 can belong to the 2026 season.
- Pricing is `free`, `paid`, or `unknown`; unknown never means free.
- Verify against the official organizer/city source; record URL, verification date and notes. Only mark the event verified when its dated schedule is supported. Missing facts remain explicit. Verification is manual, not automatic expiration or source monitoring.
- Create/manage venues in **Venues**. Enter a verified street address, save, and request **Save & geocode**. Set `GEOCODER_USER_AGENT` to identify this app and include your contact first. Nominatim calls are serialized, rate-limited to at most one per 1.1 seconds, and permanently cached (including no-match results). No autocomplete, startup lookup loop, or scheduled bulk requests. Change the service URL through `GEOCODER_URL` if needed.
- Inspect the geocoder's returned source; address interpolation or a street match can be approximate. Correct both coordinates manually and record the source. Changing the venue address/city in the editor clears old coordinates. Events without known locations stay visible and are counted as awaiting a location.
- Existing coordinates are never silently refreshed. To request again after an address correction, save that correction first. Cached results for the exact same address remain permanent; a no-match can be resolved with a better address or manual sourced coordinates.

Map attribution follows [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/). Geocoding follows the [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/); no tile prefetch or offline bulk downloads. Map view center is a regional viewport, not a fabricated event location.

### Import additional events

**Admin → Import / export** accepts `.json` and `.csv` up to 4.5 MB (2,000 events per import). Export a backup before importing. Review the file preview, then apply it. The entire import validates before saving; any invalid record or missing venue reference rolls back the batch. IDs are upsert keys: matching IDs are replaced, new IDs added. Absent IDs are retained. Imports replace complete matching records, so preserve coordinates and complete occurrence lists in files you import.

The canonical JSON shape is `{"venues": [...], "events": [...]}`; see `data/seed.json` for an example. An empty `venues` list is allowed when all referenced venues already exist. Verified records require a source URL, verification date and at least one dated occurrence.

CSV has one row per event with the same scalar fields as JSON. `occurrences` is a JSON array in one quoted cell; `venue_json` is the attached venue object (or `null`). Export a CSV to get the precise headers and quoting. CSV exports include attached venues; JSON additionally preserves unused venues. Text cells that could be spreadsheet formulas are prefixed with an apostrophe and restored by the importer. Prefer JSON for complete backups or editing outside a spreadsheet.

Future seasons require adding records with a new `season`, using new unique IDs. There is no annual code change, automatic date rollover, or assumption that this year's date repeats next year. The year selector includes all saved seasons plus the current and next year.

## Backup and restore

A JSON export preserves events/venues. A SQLite backup also preserves geocode caches, schema version and settings. Never copy only the `.sqlite3` file while the app is writing; WAL data may be outside that file. Use SQLite's backup API:

```sh
docker compose exec app python -m app.manage backup /data/backups/holiday-2026-11-10.sqlite3
```

Use a unique filename. Keep a copy of the backup outside the NAS and preserve `.env` separately with appropriate access restrictions. Backup files contain local application data and should stay private.

Restore with the app stopped; first make a fresh backup of current data as above:

```sh
docker compose stop app
docker compose run --rm --no-deps app python -m app.manage restore /data/backups/holiday-2026-11-10.sqlite3
docker compose up -d
```

Restore checks database integrity and revokes administrator sessions. Do not run another instance during restore. The next normal startup applies pending migrations. Versioned SQL files in `backend/migrations` are applied transactionally once, recorded in `schema_migrations`. Back up before updates:

```sh
docker compose pull app
docker compose up -d --wait app
```

Seeding runs only once per new database. Restarting/rebuilding never re-adds deleted seed events or overwrites administrator edits. Changing `seed.json` does not update an existing database; use a reviewed import instead.

### Credentials

`ADMIN_PASSWORD` is hashed with Argon2 in memory at startup. Alternatively use `PYTHONPATH=backend uv run python -m app.manage hash-password` to generate a hash and set `ADMIN_PASSWORD_HASH` in `.env` (single-quoted; leave `ADMIN_PASSWORD` empty). Direct backend deployments also accept `ADMIN_PASSWORD_FILE` for a mounted secret; add that mount and environment key in a Compose override if desired. Never commit `.env` or secrets. Sign-in uses an HttpOnly SameSite=Strict session cookie, expiring after eight hours, hashed session tokens in SQLite, CSRF tokens for writes, same-origin checks and per-client login limits (five attempts per 15 minutes). One worker serializes this small LAN service and geocoding rate limiter.

## Data limitations

The supplied list is a starting calendar, not proof of organizer schedules. The seed includes official-source checks dated November 10, 2026, and preserves unresolved records. Some venues, times, admission prices and run dates remain unknown. Check `docs/SOURCES.md` and each event's notes. Unknown locations are excluded from markers; unknown dates are excluded from the calendar. No source refresh runs automatically. NAS installation itself requires access to the NAS; local Docker verification does not establish deployment there.
