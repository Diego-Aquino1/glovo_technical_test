FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY services/mcp-server/pyproject.toml .
RUN uv sync --no-dev --no-install-project

COPY services/mcp-server/app/ app/
RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8002

CMD ["python", "-m", "app.main"]
