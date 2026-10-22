# CipherVault Docker image (backend serves API + the built frontend).
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY --from=web /web/dist ./frontend/dist
COPY storage ./storage
COPY scripts ./scripts

ENV APP_PORT=8413     STORAGE_DIR=/app/storage/encrypted     DATABASE_URL=postgresql+psycopg://ciphervault:ciphervault@db:5432/ciphervault

EXPOSE 8413

# NOTE: inside a container the server must listen on all interfaces so Docker
# can publish it on the host's localhost port (see docker-compose ports:
# "127.0.0.1:8413:8413"). Local (non-Docker) runs bind 127.0.0.1 via run.bat.
CMD ["sh", "-c", "python -c \"from backend.app.db.database import init_db; init_db()\" && uvicorn backend.app.main:app --host 0.0.0.0 --port ${APP_PORT:-8413}"]
