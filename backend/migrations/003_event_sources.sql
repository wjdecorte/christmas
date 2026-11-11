ALTER TABLE discovery_sources ADD COLUMN target_event_id TEXT;
CREATE INDEX discovery_target_event ON discovery_sources(target_event_id);
