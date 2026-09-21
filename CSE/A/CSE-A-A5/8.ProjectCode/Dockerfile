# CipherGuard Shield — Dockerfile
FROM python:3.11-slim

# Avoid .pyc, unbuffered logs, no pip cache
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (build tools for xgboost/light build if needed, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy codebase
COPY cipherguard ./cipherguard
COPY web ./web
COPY data ./data
COPY models ./models
COPY reports ./reports
COPY app.py .

# Ensure data/models/reports exist even if empty (training can regenerate)
RUN mkdir -p data/raw models reports

EXPOSE 8000

# Healthcheck hits localhost inside container (container's own 127.0.0.1)
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/api/health || exit 1

# Note: inside Docker we bind to 0.0.0.0 so the host can reach the container via -p 8000:8000.
# For local non-Docker runs, the app binds to 127.0.0.1 as documented in HOW_TO_RUN.md.
CMD ["python", "-m", "uvicorn", "cipherguard.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
