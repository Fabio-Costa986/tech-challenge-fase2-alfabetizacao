# Imagem única: Cloud Run Jobs (python -m alfab <comando>) e o event-ingestor (python -m alfab serve).
FROM python:3.12.8-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ALFAB_ROOT=/app \
    DBT_SEND_ANONYMOUS_USAGE_STATS=false

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install -e .

COPY config ./config
COPY dbt ./dbt
COPY sql ./sql
COPY analises ./analises

RUN useradd --create-home app && chown -R app /app
USER app

ENTRYPOINT ["python", "-m", "alfab"]
