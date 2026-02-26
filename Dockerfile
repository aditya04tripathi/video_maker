FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

RUN find /etc -name "policy.xml" -exec sed -i 's/none/read,write/g' {} +

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root user (Celery emits SecurityWarning when running as uid=0)
RUN groupadd -r celery && useradd -r -g celery -d /app celery \
    && chown -R celery:celery /app
USER celery

# Default: run the Celery worker
# Override via docker-compose command for beat/other entrypoints
CMD ["celery", "-A", "src.celery_app:celery_app", "worker", "--loglevel=info", "--concurrency=1"]
