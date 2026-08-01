# syntax=docker/dockerfile:1.7

# --- build the static frontend ---
FROM node:20-bookworm AS frontend
WORKDIR /app/web
COPY web/package.json web/package-lock.json* ./
RUN npm ci
COPY web/ ./
RUN npm run build

# --- serve + refresh ---
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WF_DATASET_OUT=/app/dist/data/dataset.json
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
COPY pipeline/requirements.txt pipeline/requirements.txt
RUN pip install --no-cache-dir -r pipeline/requirements.txt
COPY --from=frontend /app/web/dist ./dist
COPY pipeline/ ./pipeline
COPY space/ ./space
RUN chmod +x space/refresh.sh
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app
EXPOSE 7860
CMD ["python", "space/server.py"]
