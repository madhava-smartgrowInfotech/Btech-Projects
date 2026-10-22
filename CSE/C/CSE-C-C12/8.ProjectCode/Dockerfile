FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python scripts/prepare_data.py && python scripts/build_index.py
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
