# docker/Dockerfile

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENV DB_HOST=postgres \
    DB_PORT=5432 \
    DB_NAME=ecommercedb \
    DB_USER=admin \
    DB_PASSWORD=password \
    APP_ENV=docker \
    LOG_LEVEL=INFO

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "print('healthy')" || exit 1

CMD ["python", "scripts/pipeline/orchestrator.py"]
