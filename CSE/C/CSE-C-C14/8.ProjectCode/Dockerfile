FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENV VERIVISION_PORT=5000
EXPOSE 5000

# NOTE: the Flask process binds to 127.0.0.1 per the product's local-only
# configuration. When running inside Docker, localhost means the container's
# own loopback interface; the port is published to the host's localhost via
# `-p 127.0.0.1:5000:5000`, so the app remains accessible only from the host
# machine and is not exposed on the wider network.
CMD ["python", "run.py"]
