ALTER TABLE events ADD COLUMN status TEXT NOT NULL DEFAULT 'scheduled';
CREATE TABLE discovery_sources (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL, kind TEXT NOT NULL,
 city TEXT NOT NULL, keywords TEXT NOT NULL, link_prefix TEXT NOT NULL DEFAULT '',
 enabled INTEGER NOT NULL DEFAULT 1, interval_hours INTEGER NOT NULL DEFAULT 12,
 next_check INTEGER NOT NULL DEFAULT 0, last_checked TEXT, last_error TEXT NOT NULL DEFAULT '',
 last_result TEXT NOT NULL DEFAULT '', lease_until INTEGER NOT NULL DEFAULT 0,
 checked_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE source_observations (
 source_id TEXT NOT NULL REFERENCES discovery_sources(id), external_id TEXT NOT NULL,
 fingerprint TEXT NOT NULL, payload TEXT NOT NULL, observed_at TEXT NOT NULL,
 PRIMARY KEY(source_id,external_id)
);
CREATE TABLE review_proposals (
 id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES discovery_sources(id), external_id TEXT NOT NULL,
 kind TEXT NOT NULL, event_id TEXT, fingerprint TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
 before_json TEXT NOT NULL, proposed_json TEXT NOT NULL, venue_json TEXT,
 evidence_url TEXT NOT NULL, evidence_text TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL, reviewed_at TEXT, base_updated_at TEXT,
 UNIQUE(source_id,external_id,fingerprint)
);
CREATE INDEX review_status ON review_proposals(status,created_at);
CREATE TABLE review_audit (
 id INTEGER PRIMARY KEY, proposal_id TEXT NOT NULL, action TEXT NOT NULL, event_id TEXT,
 before_json TEXT NOT NULL, after_json TEXT NOT NULL, reviewed_at TEXT NOT NULL
);
INSERT INTO discovery_sources(id,name,url,kind,city,keywords,link_prefix) VALUES
 ('kennesaw-calendar','City of Kennesaw','https://www.kennesaw-ga.gov/events/list/','jsonld','Kennesaw','christmas,holiday,santa,holly,tree lighting,glimmer,nutcracker','/kennesaw-event/'),
 ('alpharetta-calendar','Awesome Alpharetta','https://www.awesomealpharetta.com/events/','jsonld','Alpharetta','christmas,holiday,santa,noel,ice,lighting,nutcracker','/event/');

INSERT INTO discovery_sources(id,name,url,kind,city,keywords,link_prefix) VALUES
 ('canton-calendar','Explore Canton','https://explorecantonga.com/events/annual-events/','jsonld','Canton','christmas,holiday,santa,noel,tree lighting,grinch,polar,rink','/events/'),
 ('woodstock-arts','Woodstock Arts','https://woodstockarts.org/events/','jsonld','Woodstock','christmas,holiday,noel,nutcracker','/events/'),
 ('atlanta-pops','Atlanta Pops schedule','https://atlantapops.org/concerts-events/','page','Waleska','christmas,holiday,noel',''),
 ('woodstock-parks','Woodstock Parks holiday page','https://woodstock.recdesk.com/Community/Program/Detail?programId=2646','page','Woodstock','christmas,holiday,parade',''),
 ('georgia-symphony','Georgia Symphony Holiday Pops','https://www.georgiasymphony.org/event/holiday-pops-4/','page','Marietta','christmas,holiday,pops',''),
 ('falany-noel','Falany Nashville Noel','https://thefalany.showare.com/eventperformances.asp?evt=9','page','Waleska','christmas,holiday,noel','');
