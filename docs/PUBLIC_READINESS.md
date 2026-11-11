# Preparing the holiday guide for friends

Jason chose anonymous read-only event pages: anyone who obtains the link can read them. A link is not a secret access control. Administrator sign-in is separate; public visitors cannot add sources, see review proposals/history, approve changes, import/export the administration dataset or edit events.

This change prepares the application; it does not configure DNS, expose NAS ports, create a tunnel, or change the running NAS. Decide the public hostname and gateway before enabling public mode. The NAS's current LAN installation can continue with `PUBLIC_MODE=false`.

## Public mode contract

Set the following only when an HTTPS gateway is ready and preserves the public Host header:

```dotenv
PUBLIC_MODE=true
PUBLIC_ORIGIN=https://holidays.example.com
PUBLIC_INDEXABLE=false
ADMIN_PASSWORD='a-unique-strong-password-at-least-16-characters'
```

Replace the example hostname. `PUBLIC_ORIGIN` is one exact HTTPS origin, including a nonstandard public port if used; no path, wildcard or embedded credentials. Public mode refuses to start without it or with a short plain password. Secret-file passwords are checked against the same 16-character minimum. Supported Argon2 hashes can be generated with the maintenance command and quoted in `.env`; remove conflicting password settings. The app validates the configured hash at startup. Use a unique generated administrator credential, never a password shared with visitors.

Public mode:

- Accepts only the configured Host; mismatches are rejected. The internal loopback health probe remains available.
- Checks browser write origins against that exact public HTTPS origin in addition to CSRF tokens and SameSite cookies.
- Forces Secure + HttpOnly + SameSite=Strict admin cookies, even if the legacy `COOKIE_SECURE` variable is false. HTTPS must work before admin sign-in can succeed.
- Adds HSTS, no-sniff, frame restrictions, a self-hosted-script CSP and a restrictive Permissions Policy.
- Defaults to `noindex, nofollow` through an HTTP header. Set `PUBLIC_INDEXABLE=true` only if you intentionally want search indexing; indexing controls do not make pages private.
- Keeps public reads anonymous, rejects all unauthenticated administrative APIs, limits login attempts and bounds request bodies. Sessions expire after eight hours and are revoked on server restart.

TLS terminates at the gateway; the app may receive HTTP over a private connector/network. Do not expose that upstream port publicly. The app does not trust arbitrary forwarded client-IP or scheme headers; behind one gateway, login throttling may group clients under the gateway address. One administrator is supported. Edge login throttling/bot controls and, if desired, an additional identity policy for admin paths belong at the chosen gateway. Do not treat app hardening as a guarantee against volumetric attacks or a substitute for keeping NAS/Docker dependencies current.

## Deployment discussion

Retain the established **GitHub Actions → GHCR image → NAS Compose pull** release pattern. The public-access layer is a separate decision:

| Approach | What friends need | Tradeoff |
| --- | --- | --- |
| NAS + Cloudflare Tunnel + custom HTTPS hostname | A browser link | No inbound NAS port forwarding; requires a Cloudflare account/domain configuration and trusts that provider as the public edge. NAS/home internet availability still matters. |
| NAS + Synology HTTPS reverse proxy | A browser link | Keeps the access layer under your control, but needs DNS/certificates, suitable internet connectivity and inbound firewall/router rules. Greater home-network exposure to manage. |
| Small hosted server running the same Compose image | A browser link | Separates public hosting from the home NAS, with recurring hosting/backup/maintenance work. Data would live on that server rather than the NAS. |

For a small anonymous-read guide, the first option is a practical candidate when a Cloudflare-managed domain/account is acceptable. The third is preferable if home-network separation or uptime matters more than NAS hosting. No option has been provisioned or selected by this preparation work. A VPN is useful for private administrator maintenance but would require friends to install/sign in, which differs from Jason's chosen browser-link access.

Before a public launch: choose hostname/gateway; back up SQLite; configure public origin/credential; limit the app port to the private gateway/LAN; verify HTTPS, Host/origin rejection, anonymous event viewing, protected review APIs and secure-cookie sign-in through the actual gateway; then check restored backups and source-check status. Keep admin/data/DSM ports off the public router. Use the optional admin identity restriction at the edge if available, covering `/api/auth/*`, `/api/admin/*` and any separately exposed admin UI path. The current admin screen is part of the SPA; protecting its APIs is essential.

References: [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/), [Synology reverse proxy](https://kb.synology.com/en-global/DSM/help/DSM/AdminCenter/application_appportalias), [GHCR registry access](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).
