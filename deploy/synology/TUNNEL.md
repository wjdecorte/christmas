# Cloudflare Tunnel on the NAS

Public hostname: **christmas.decorteindustries.com**. The app and SQLite remain on the NAS; visitor requests travel through Cloudflare to this origin. No router forwarding or DSM exposure is required. Existing company-site DNS records stay unchanged.

## Configure the tunnel

In Cloudflare's tunnel dashboard, create a remotely managed **Cloudflared** tunnel named `christmas-nas`. Choose Docker for the connector. Store only its tunnel token in `/volume1/docker/christmas-events/secrets/cloudflare-tunnel-token`, with the directory mode 700 and file mode 600, owned by the configured `APP_UID` (currently 1026). Never commit or paste the token into chat. The Compose connector uses a token file rather than a command-line credential.

Add one published application route:

- Hostname: `christmas.decorteindustries.com`.
- Service type: HTTP; URL: `app:8090` (connector and app share the Compose network).
- HTTP Host Header: `christmas.decorteindustries.com`.
- No path restriction; no additional hostname routes.

Check that the hostname is unused before saving. Do not replace an existing DNS record without reviewing its purpose. Do not change the root domain, `www`, nameservers, or company-site records. Cloudflare provisions the hostname's tunnel DNS route and edge HTTPS certificate. Wait until the certificate is active before sharing the link.

## Start the connector

Copy `compose.tunnel.yaml` beside the existing NAS `compose.yaml`. Preserve `.env`, UID/GID, data path and port. Public mode requires the existing admin password to have at least 16 characters (or a valid configured Argon2 hash). If startup rejects the password length, change it privately on the NAS before retrying. Do not disclose it to the agent.

Back up before changing the deployment:

```sh
cd /volume1/docker/christmas-events
sudo /usr/local/bin/docker compose exec -T app python -m app.manage backup /data/backups/before-tunnel-UNIQUE-TIMESTAMP.sqlite3
sudo /usr/local/bin/docker compose -f compose.yaml -f compose.tunnel.yaml config --quiet
sudo /usr/local/bin/docker compose -f compose.yaml -f compose.tunnel.yaml pull app cloudflared
sudo /usr/local/bin/docker compose -f compose.yaml -f compose.tunnel.yaml up -d --wait
sudo /usr/local/bin/docker compose -f compose.yaml -f compose.tunnel.yaml ps
```

Replace the backup placeholder with a unique timestamp. Use both Compose files for subsequent updates, or select both in Container Manager. `CLOUDFLARED_IMAGE` can pin a tested official connector version/digest; updates require pulling and recreating the container. No image build is needed on the NAS. This override defaults to the tested app commit; set `CHRISTMAS_IMAGE` to a newer tested commit tag when upgrading. Always pull both services before recreating them to avoid reusing an old cached `latest` image.

Public mode accepts only the configured hostname. The direct LAN-IP site will return an unrecognized-host error; use the HTTPS public URL for browsing and admin sign-in. Internal loopback health checks remain available. Secure admin cookies require HTTPS. A server restart signs the administrator out. Visitors do not need accounts.

## Verify and recover

Verify public HTTPS, event count, CSS/icon/map, admin sign-in/sign-out, a 401 for anonymous `/api/admin/review`, rejection of an incorrect Host, and a healthy tunnel in Cloudflare. Review APIs must not be cached; preserve application Cache-Control headers and do not add a Cache Everything rule. Search indexing stays disabled by default. The app's existing admin authentication/CSRF remain active; a separate Cloudflare Access policy for admin APIs can be added later without gating public event reads.

If activation fails, inspect container logs without displaying tokens. Restore the LAN deployment by stopping the connector and running only the base Compose file:

```sh
sudo /usr/local/bin/docker compose -f compose.yaml -f compose.tunnel.yaml stop cloudflared
sudo /usr/local/bin/docker compose -f compose.yaml up -d --wait app
```

This override does not change `.env` or SQLite. With base `PUBLIC_MODE=false` (the current LAN setting), direct LAN access returns. Pause/remove the published tunnel route in Cloudflare if abandoning it. Never use `down -v` or delete the data directory.

References: [Create a tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/), [token-file parameter](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/run-parameters/).
