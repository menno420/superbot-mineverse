# Deployment image for the mineverse web host (Railway service `web`).
#
# Why this file exists: the backend is deliberately stdlib-only (no
# requirements.txt / pyproject), so buildpack auto-detection (Railpack /
# Nixpacks) cannot classify the app and the build fails before it starts —
# observed live on Railway 2026-07-12 (BUILD_IMAGE failed in <6s, project
# superbot-mineverse). A Dockerfile makes the build deterministic.
#
# The server binds HOST (default 127.0.0.1 for local dev); containers must
# accept external traffic, hence HOST=0.0.0.0 here. Railway injects PORT.
FROM python:3.10-slim

WORKDIR /app
COPY . .

ENV HOST=0.0.0.0
EXPOSE 8000

CMD ["python3", "server/app.py"]
