# QuantPulse backend image (CPU-only, Python 3.11)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    HF_HUB_OFFLINE=0

WORKDIR /app

# System deps for scientific stack + prophet
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY backend ./backend
COPY data ./data
COPY artifacts ./artifacts
COPY frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"]
