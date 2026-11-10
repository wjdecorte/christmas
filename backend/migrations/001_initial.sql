CREATE TABLE venues (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, address TEXT NOT NULL DEFAULT '', city TEXT NOT NULL,
 latitude REAL CHECK(latitude BETWEEN -90 AND 90), longitude REAL CHECK(longitude BETWEEN -180 AND 180),
 coordinate_source TEXT NOT NULL DEFAULT '', geocoded_at TEXT,
 CHECK ((latitude IS NULL) = (longitude IS NULL))
);
CREATE TABLE events (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, venue_id TEXT REFERENCES venues(id) ON DELETE RESTRICT,
 city TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', price_type TEXT NOT NULL DEFAULT 'unknown',
 price_details TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '', verified INTEGER NOT NULL DEFAULT 0,
 last_verified TEXT, last_checked TEXT, verification_notes TEXT NOT NULL DEFAULT '', featured INTEGER NOT NULL DEFAULT 0,
 season INTEGER NOT NULL, schedule_notes TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
);
CREATE TABLE occurrences (
 id INTEGER PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
 start_date TEXT NOT NULL, end_date TEXT NOT NULL, start_time TEXT, end_time TEXT,
 CHECK(end_date >= start_date)
);
CREATE INDEX occurrences_dates ON occurrences(start_date,end_date);
CREATE INDEX events_season ON events(season,category,city);
CREATE TABLE sessions (token_hash TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires_at INTEGER NOT NULL);
CREATE TABLE login_attempts (ip TEXT NOT NULL, attempted_at INTEGER NOT NULL);
CREATE INDEX login_attempts_time ON login_attempts(attempted_at);
CREATE TABLE geocode_cache (query TEXT PRIMARY KEY, latitude REAL, longitude REAL, display_name TEXT, fetched_at TEXT NOT NULL);
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
