FROM python:3.12-slim

# BACKEND_HOST/BACKEND_PORT: the container serves the original dashboard on 5000 (a project .env cannot override these).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BACKEND_HOST=0.0.0.0 \
    BACKEND_PORT=5000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Train at build time when possible; runtime entrypoint re-checks.
RUN python ml/train_model.py || echo "Training deferred to container start"

EXPOSE 5000

CMD ["python", "app.py"]
