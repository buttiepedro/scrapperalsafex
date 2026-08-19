FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    TZ=America/Argentina/Buenos_Aires

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron tzdata ca-certificates \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY docker/crontab /app/crontab
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod 0644 /app/crontab \
    && chmod +x /usr/local/bin/entrypoint.sh \
    && crontab /app/crontab \
    && mkdir -p /app/output /app/logs

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
