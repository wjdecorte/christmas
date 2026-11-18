# Prompt for the NAS-wide container updater project

Build a shared container-image monitoring and update service for my Synology NAS,
covering multiple independent Docker Compose projects. Keep this infrastructure
in its own project/repository, separate from Christmas and Picker (NFL Picks).

Evaluate and use What's Up Docker (WUD) as the preferred replacement for archived
containrrr/watchtower. Verify its current official release, image, Synology Docker
API compatibility, and documentation before implementation. Alternatives considered:
Diun for notifications only; Nicholas Fedor's Watchtower fork for the closest
Watchtower workflow. WUD is preferred for its dashboard, notifications and optional
Compose-aware updates. Do not use the archived original Watchtower image.

Requirements:
- One NAS-wide service, with a LAN-only dashboard and explicit per-container opt-in.
- Start with monitoring/notifications only. Update triggers must initially be
  disabled, including manual update actions until the backup path is ready.
- Prepare an overnight update window in America/New_York, but confirm notification
  destination and preferred schedule before enabling them.
- Later permit automatic updates for selected apps; exclude databases and
  infrastructure (including the Cloudflare connector) unless deliberately enrolled.
- For updates: serialize per project, back up application data first, preserve
  credentials/volumes/ports/Compose overrides, validate health, record the old
  image digest, and provide failure notifications and tested recovery. A Compose
  file backup is not a SQLite backup. Do not assume image rollback reverses a
  database migration; document migration compatibility and restore procedure.
- Minimize Docker API access using a suitable socket proxy if supported, while
  recognizing that update permissions are powerful. Keep registry credentials
  private; private GHCR access must be explicitly configured for WUD as necessary.
- Use prebuilt images and Compose. Follow the Picker NAS deployment standard in
  ProjectOS; do not build application images on the NAS or reset existing data.
- Inspect existing projects read-only first. Prepare reviewable configuration and
  tests; do not deploy, change live image pins or enable automatic updates until
  I authorize activation in this new project.

Christmas integration already prepared, NOT deployed or merged:
- Repo: /Users/jason/Projects/christmas, GitHub wjdecorte/christmas.
- Branch: codex/nas-updater-readiness. Inspect the branch and its current commit.
- Workflow adds moving ghcr.io/wjdecorte/christmas:stable only for tested main
  publications, preserving latest and immutable sha-<full-commit> tags. Feature
  branch dispatch cannot publish images. stable is not published by this branch.
- Root compose.yaml matches deploy/synology/compose.yaml; default image becomes
  stable, with CHRISTMAS_IMAGE still authoritative.
- WUD_WATCH=false by default; opt-in labels include wud.watch.digest=true and a
  stable-only tag filter. cloudflared explicitly sets wud.watch=false.
- deploy/synology/compose.tunnel.yaml inherits the base image rather than an old
  fallback pin. Public-mode security remains enabled.
- Live NAS currently stays on sha-51360377e424ddf956c10d43bbaac928ba4b391e.
  Do not change its .env yet. Existing pins prevent following stable automatically.
- NAS: SSH alias synology, 10.72.0.5:2222, user jadministrator. Docker requires
  interactive sudo; never ask for the password in chat or change privilege rules.
- Christmas deployment: /volume1/docker/christmas-events; BOTH compose.yaml and
  compose.tunnel.yaml are required. Data: /volume1/docker/christmas-events/data;
  container database /data/events.sqlite3; APP_UID=1026, APP_GID=100; LAN port8094.
- Public hostname https://christmas.decorteindustries.com uses Cloudflare Tunnel;
  leave its route, token and company DNS unchanged.
- SQLite backup command (using both Compose files):
  docker compose -f compose.yaml -f compose.tunnel.yaml exec -T app python -m app.manage backup /data/backups/<unique-name>.sqlite3
- Before integrating auto-updates, solve Compose/.env consistency for image
  references and multi-file overrides. Do not let WUD update only a container or
  literal YAML value while .env still selects an older pinned image.

Read the new project's AGENTS.md and ProjectOS instructions. Inspect the Christmas
branch and deployment guide, then propose the exact initial monitoring setup and
remaining decisions. Keep all live applications unchanged during preparation.

Official references:
- https://github.com/getwud/wud
- https://getwud.app/docs/configuration/triggers/
- https://getwud.app/docs/configuration/triggers/docker-compose/
- https://getwud.app/docs/configuration/triggers/command/
- https://github.com/crazy-max/diun
- https://github.com/nicholas-fedor/watchtower
