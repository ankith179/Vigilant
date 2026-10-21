FROM node:24-bookworm-slim AS frontend
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-core.txt ./
RUN pip install --no-cache-dir -r requirements-core.txt
RUN useradd --uid 10001 --create-home vigilant
COPY --chown=vigilant:vigilant . .
COPY --from=frontend --chown=vigilant:vigilant /ui/dist ./frontend/dist
USER vigilant
ENV VIGILANT_DB=sqlite:///data/vigilant.db VIGILANT_FREE_ONLY=1
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=5)"
CMD ["sh", "-c", "python scripts/restore_checkpoint.py && python scripts/sync_dashboard.py && exec python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --workers 1"]
