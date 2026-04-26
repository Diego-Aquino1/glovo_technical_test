FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY services/erp-service/pyproject.toml .
RUN uv sync --no-dev --no-install-project

COPY services/erp-service/alembic.ini .
COPY services/erp-service/alembic/ alembic/
COPY services/erp-service/app/ app/
COPY services/erp-service/entrypoint.sh .
RUN chmod +x entrypoint.sh

COPY db/seed.sql db/seed.sql

RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8001

ENTRYPOINT ["./entrypoint.sh"]
