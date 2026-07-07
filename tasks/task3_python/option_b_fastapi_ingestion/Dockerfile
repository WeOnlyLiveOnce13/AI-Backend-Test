FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

COPY . .

CMD ["sh", "-c", "uv run --no-dev uvicorn tasks.task3_python.option_b_fastapi_ingestion.app.main:app --host \"$API_HOST\" --port \"$API_PORT\""]
