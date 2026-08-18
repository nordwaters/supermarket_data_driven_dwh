FROM apache/superset:latest

USER root

# Устанавливаем системные зависимости для работы с сетью и Postgres
RUN apt-get update && apt-get install -y libpq-dev gcc --no-install-recommends \
    && pip install --no-cache-dir psycopg2-binary pg8000 \
    && apt-get purge -y --auto-remove gcc \
    && rm -rf /var/lib/apt/lists/*

USER superset
