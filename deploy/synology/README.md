# Run Christmas on Synology

This uses the same deployment pattern as Picker: GitHub Actions tests the application, builds amd64 and arm64 images on native runners, and publishes **ghcr.io/wjdecorte/christmas**. The NAS pulls a prebuilt image. It does not need source code, Node, Python, uv, or a local Docker build.

`latest` follows `main`; `sha-<full-commit>` pins a build. Version tags such as `v1.2.3` also publish `1.2.3` and `1.2`, without replacing `latest`. Publishing uses the workflow's built-in `GITHUB_TOKEN`. A new package stays private by default. Check the [image workflow](https://github.com/wjdecorte/christmas/actions/workflows/image.yaml) for a successful publication before trying the first pull.

## 1. Registry login

For a private package, sign in **on the NAS** using the same GHCR login as Picker, or:

```sh
docker login ghcr.io -u wjdecorte
```

Enter a GitHub classic token with `read:packages` and access to the package at the password prompt. Do not put it in `.env`, Compose, or Git. If the NAS is already logged in for Picker and its token can read this package, no new login is needed. Public packages can be pulled anonymously; this workflow does not change visibility.

## 2. Copy only the deployment files

Copy **compose.yaml** and **.env.example** from this directory to a NAS project folder, for example `/volume1/docker/christmas-events-app`. These copies match the root files. Keep persistent SQLite data separately at `/volume1/docker/christmas-events`.

On the NAS, using your existing SSH setup (Picker documents port 2222), or the equivalent File Station/Container Manager controls:

```sh
cd /volume1/docker/christmas-events-app
cp .env.example .env
chmod 600 .env
openssl rand -hex 24
```

Set `ADMIN_PASSWORD` in `.env` to a strong unique value (12+ characters; the generated hex is suitable). Set `GEOCODER_USER_AGENT` with your contact. Optionally set `BIND_ADDRESS` to the NAS LAN address. Leave `PORT=8090` unless another service uses that port. The image is configurable through `CHRISTMAS_IMAGE`.

The container runs as UID/GID 1000 by default. Create and grant access to the **new dedicated data directory**, not a shared folder containing other services:

```sh
sudo mkdir -p /volume1/docker/christmas-events
sudo chown 1000:1000 /volume1/docker/christmas-events
sudo chmod 700 /volume1/docker/christmas-events
```

Alternatively configure `APP_UID` and `APP_GID` for a dedicated NAS user and grant it access through Synology permissions. Preserve existing SQLite data and credentials if updating an installation.

## 3. Pull and start

```sh
docker compose pull
docker compose up -d --wait
docker compose ps
```

Or create a Container Manager Project from this folder and the Compose file, then start it. There is no `build:` entry in the NAS configuration.

Open `http://YOUR_NAS_IP:8090` on your LAN. Select Admin and use the configured password. Only the web port is exposed. SQLite stays in the data directory; startup applies migrations and seeds a new database once. No cloud runtime account is needed. The first deployment/pull needs registry access; the app needs outbound internet only for map tiles and manual geocoding/source checks. Keep router forwarding disabled and limit the NAS firewall to your home subnet.

## 4. Back up and update

Use a new filename each time:

```sh
docker compose exec app python -m app.manage backup /data/backups/before-update-2026-11-10.sqlite3
docker compose pull app
docker compose up -d --wait app
docker compose ps
```

No source copying or rebuilding on the NAS is needed for updates. To pin or roll back code, set `CHRISTMAS_IMAGE` to a previous `sha-...` tag or image digest, then pull and recreate. A schema rollback may also need a matching backup restore; replacing the image does not undo migrations. Never delete the data directory or use `down -v` for an update.

Restore with the app stopped:

```sh
docker compose stop app
docker compose run --rm --no-deps app python -m app.manage restore /data/backups/before-update-2026-11-10.sqlite3
docker compose up -d --wait
```

See the root README for importing existing events, backup/restore details, credentials, and manual verification. An existing Mac database is not bundled in the image. Transfer its SQLite backup separately and restore into an isolated NAS installation before selecting that installation as the authoritative writer. Do not copy only an actively written SQLite main file; use the backup command.

References: [GHCR authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry), [Docker multi-platform builds](https://docs.docker.com/build/ci/github-actions/multi-platform/).
