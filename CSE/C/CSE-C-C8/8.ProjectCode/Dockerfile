FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./
RUN python scripts/prepare_dataset.py && python scripts/train_model.py && python scripts/make_demo_pdf.py
EXPOSE 8408
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8408"]
