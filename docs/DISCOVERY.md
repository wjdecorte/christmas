# Automatic discovery and source review

Public event pages remain readable without a visitor account. Source configuration, discoveries, approval history, imports and editing require administrator sign-in and CSRF protection.

## How it works

The application checks a curated list of official calendars and organizer pages every 12 hours while its single Docker process is running, independently of browser visits. The default approved sources cover Kennesaw, Alpharetta, Canton and Woodstock event listings, plus monitored organizer pages for Atlanta Pops, Woodstock Parks, Georgia Symphony and the Falany. In Admin → Review, add further official HTTPS sources for other towns/venues. Discovery is bounded source checking, not a paid search API or an unrestricted web crawler.

`DISCOVERY_ENABLED=true` enables the background worker. Set it to false to pause all network checks; it does not disable reviewing existing proposals. Each source also has an enable/pause switch and a 6–168 hour interval. Checks start after a short startup delay. **Check now** queues work; it does not publish anything and cannot queue a running check. Manual checks have a one-minute cooldown. The checker serializes work, spaces requests to a host, honors robots.txt/crawl-delay, limits page/record/body counts and timeouts, validates TLS, and blocks private/reserved/loopback destinations, including DNS resolutions and redirects. It connects to the validated numeric IP with the original TLS hostname; ambient HTTP proxy settings are not used. A persistent lease prevents duplicate workers from checking a source concurrently and expires after an interrupted run.

Formats:

- **Event pages / JSON-LD:** extracts source-stated Schema.org Event facts from listing/detail pages. The optional path prefix follows up to eight links on the same approved host. Existing published source URLs on that host are also checked, within a total 16 linked-page budget per run. Duplicate listing/detail identities are consolidated by event URL.
- **Calendar feed / iCalendar:** reads VEVENT dates, titles, locations, URLs and cancellation status. Date-only DTEND is interpreted as exclusive, as required by RFC 5545. Feeds with unexpanded RRULE/RDATE or recurrence overrides are explicitly rejected instead of importing incomplete schedules. Use an expanded feed, event pages, or manual recurring dates for those sources.
- **Monitor one event page:** captures a text baseline for an existing event's exact source URL. Later text changes or missing pages become review signals. Pages without structured dates require the administrator to make the actual event edits. The first successful text capture creates a baseline, not a claim that the event is verified.

New holiday discovery is limited to November, December and January in the current/next calendar year, filtered by source keywords. General office-closure records are skipped. A source is not exhaustive: pagination budgets, missing structured data, robots rules, blocked requests and JavaScript-only content can limit coverage. Errors and the last result appear beside each source. A failed check never removes published events. Missing feed items are not inferred to be cancellations.

## Review workflow

1. Open **Admin → Review**. Pending items are new discoveries, structured changes, changed page text, or unavailable source pages. No item is public yet.
2. Open **Review** and inspect the published/source comparison and original source link. Source excerpts are untrusted evidence, not instructions or proof of correctness.
3. Correct the name, city, category, season, status, admission, dates/times, description and notes. Event times are Eastern; explicit offsets are converted to Eastern. Do not infer a price or closing time that the source did not provide.
4. Inspect the proposed venue or choose a saved one. New venues start without coordinates. Geocode or correct them later in Venues. A proposal cannot silently replace coordinates or details on an existing shared venue.
5. Tick the verification checkbox only after checking the official source. Approval without that checkbox publishes an explicitly unverified event. **Approve & publish** saves the reviewed event/venue and audit entry in one transaction. **Dismiss** leaves the public record unchanged.
6. If someone edited the published event after the proposal was captured, approval stops with a conflict. **Load latest published event** reapplies the proposed differences over the current record; review them again before approving. Other manual fields are preserved. A newer source observation supersedes an older pending item; it cannot be approved accidentally from an old browser tab.

Cancellation/postponement is an explicit reviewed event status shown on public cards, calendar and detail pages. A 404/410 source page does not prove cancellation. Partial performance pages preserve other published performances; they do not establish that the rest of a series was removed. Review the full schedule before approval.

Approved/dismissed/superseded history remains available in the queue. `/api/admin/review-audit` exposes the latest approval/dismissal snapshots to authenticated administrators. Identical observed data is not repeatedly queued, including after dismissal. Sources retain identity/history; to change a URL or format, pause the old source and create a new source ID.

Public browser tabs refresh data on focus and every five minutes while visible. Admin editing is excluded from this polling. Public data changes only after approval or ordinary authenticated edits/imports.

## Storage and upgrades

Migration `002_discovery.sql` adds event status, source settings, observations, review proposals and audit history. It is additive; existing events, venues and coordinates are retained. The worker never edits published events directly. Back up the running NAS database before installing this version. SQLite backups preserve the queue and source settings; JSON/CSV exports preserve events/venues, not discovery/audit history. Restoring a backup revokes administrator sessions. Successful application startup also revokes old sessions.

References: [Schema.org Event](https://schema.org/Event), [iCalendar RFC 5545](https://www.rfc-editor.org/rfc/rfc5545).


## Additional URLs for a saved event

Open **Admin → Events → Edit → Additional sources**. Add a label and public HTTPS URL, then choose **Add URL & queue check**. Up to 20 additional sources can be attached per event. Save ordinary event edits first: checking uses the published/saved record. Sources persist independently of the editor's Save/Cancel buttons. Duplicate canonical URLs are rejected.

The checker visits only the exact approved URL and binds its suggestions to that saved event. A single structured JSON-LD Event, or a unique exact-name match on a multi-event page, can suggest changes. Ambiguous listings and pages without structured event data provide excerpts for manual review, including on their first check. Missing pages remain review signals, not automatic cancellations. Login-only/blocked pages cannot be fetched. Existing robots/TLS/public-IP/body/timeout protections apply. No Facebook login, CAPTCHA bypass, or generic AI interpretation is introduced.

Additional sources never replace the event's original public source URL automatically or on approval. All proposed edits stay in **Admin → Review** until approved. Identical observations do not repeatedly queue. Sources run every 12 hours by default; use Check now, Pause checks, or Enable checks in the event editor. Status, errors and results refresh while the editor is open. Global `DISCOVERY_ENABLED=false` pauses fetching; queueing a Check now then reports that setting must be enabled. General source settings remain available in Admin → Review.

Migration `003_event_sources.sql` adds an optional event binding to discovery sources. It does not change existing event fields or sources. Deleted events leave their source bindings intact; subsequent checks report that the linked event no longer exists, rather than discovering into unrelated events. Pause those sources. Back up SQLite before upgrading. The database backup preserves additional source associations; event JSON/CSV exports do not include private discovery-source settings.
