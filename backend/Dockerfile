FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser && mkdir -p /data/uploads && chown appuser /data/uploads
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main: app --host 0.0.0.0 --port ${PORT:-8000}"]