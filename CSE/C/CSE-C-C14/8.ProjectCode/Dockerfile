FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENV VERIVISION_HOST=0.0.0.0
ENV VERIVISION_PORT=8414
EXPOSE 8414

# The process binds 0.0.0.0 inside the container so the published port works; docker-compose
# and run-docker.bat publish it as 127.0.0.1:8414 only, so it is still reachable only from this PC.
CMD ["python", "run.py"]
