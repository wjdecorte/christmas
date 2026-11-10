# syntax=docker/dockerfile:1
FROM node:24-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.10.4 AS uv
FROM python:3.12-slim-bookworm AS runtime
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/backend DATABASE_PATH=/data/events.sqlite3
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./backend/
COPY data/seed.json ./data/seed.json
COPY --from=frontend /build/dist ./frontend/dist
RUN groupadd --gid 1000 holiday && useradd --uid 1000 --gid holiday --no-create-home holiday \
    && mkdir /data && chown holiday:holiday /data
USER 1000:1000
EXPOSE 8090
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8090/api/health',timeout=4)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "1", "--no-proxy-headers"]
