# Task 3: FastAPI Alarm Ingestion Service

This implementation builds the FastAPI alarm ingestion service. Postgres is the durable source of truth and Redis is used as a recent-events cache.

## Architecture

The app uses a small layered structure:

```text
controllers -> services -> repositories/cache -> Postgres/Redis
```

```text
app/
  main.py
  config.py
  schemas.py
  dependencies.py

  controllers/
    alarms.py

  services/
    alarm_service.py

  repositories/
    alarm_repository.py

  cache/
    recent_event_cache.py

  db/
    schema.sql
    queries/
      upsert_alarm_event.sql
      bulk_upsert_alarm_events.sql
      select_recent_alarm_events_by_camera.sql
```

The controller layer owns HTTP routing. The service layer owns workflow decisions such as cache fallback. The repository layer owns Postgres persistence and loads SQL from `.sql` files. The cache layer owns Redis sorted-set operations.

## API

### `GET /health`

Returns:

```json
{"status": "ok"}
```

### `POST /alarms`

Ingests a single alarm event.

Example:

```json
{
  "alarm_id": "ALM-1",
  "camera_id": "CAM-1",
  "timestamp": "2026-06-20T12:00:00Z",
  "alarm_type": "person",
  "metadata": {"confidence": 0.91}
}
```

### `POST /alarms/bulk`

Ingests a list of alarm events.

Returns:

```json
{"ingested_count": 3}
```

### `GET /cameras/{camera_id}/recent?limit=K`

Returns the K most recent events for a camera in chronological order.

## Persistence

The app creates this table on startup:

```sql
CREATE TABLE IF NOT EXISTS alarm_events (
    alarm_id TEXT PRIMARY KEY,
    camera_id TEXT NOT NULL,
    event_ts TIMESTAMPTZ NOT NULL,
    alarm_type TEXT NOT NULL,
    metadata JSONB,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alarm_events_camera_ts
ON alarm_events (camera_id, event_ts DESC);
```

`alarm_id` is the primary key. Ingest uses upsert semantics so retries are idempotent.

## Redis Cache

Redis stores recent events in one sorted set per camera:

```text
recent:{camera_id}
```

The sorted-set score is the event timestamp as epoch seconds. This means events can arrive out of order and still be returned in correct timestamp order.

The cache stores only the latest `RECENT_CACHE_SIZE` events per camera.

## Cache Fallback

For `GET /cameras/{camera_id}/recent?limit=K`:

1. If `K <= RECENT_CACHE_SIZE`, the service tries Redis first.
2. If Redis has enough events, it returns the cached events.
3. Otherwise it falls back to Postgres, returns the correct result, and refreshes Redis with the returned events.

Postgres remains the source of truth. Redis is only an acceleration layer.

## Configuration

Runtime configuration is injected through environment variables:

```text
DATABASE_URL
REDIS_URL
RECENT_CACHE_SIZE
```

For local development, copy the root `.env.example`:

```bash
cp .env.example .env
```

## Run Locally

From the repository root:

```bash
docker compose up -d postgres redis
uv run uvicorn tasks.task3_python.option_b_fastapi_ingestion.app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

## Run With Docker Compose

From the repository root:

```bash
docker compose --profile app up --build
```

The API is available at:

```text
http://localhost:8000
```

## Tests

Run:

```bash
uv run pytest tasks/task3_python/option_b_fastapi_ingestion/tests
```

Run linting:

```bash
uv run ruff check tasks/task3_python/option_b_fastapi_ingestion
```

## Manual Smoke Test

```bash
curl http://localhost:8000/health
```

```bash
curl -X POST http://localhost:8000/alarms \
  -H "Content-Type: application/json" \
  -d '{
    "alarm_id": "ALM-API-1",
    "camera_id": "CAM-API-1",
    "timestamp": "2026-06-20T12:00:00Z",
    "alarm_type": "person",
    "metadata": {"confidence": 0.91}
  }'
```

```bash
curl -X POST http://localhost:8000/alarms/bulk \
  -H "Content-Type: application/json" \
  -d '[
    {
      "alarm_id": "ALM-API-3",
      "camera_id": "CAM-API-1",
      "timestamp": "2026-06-20T12:02:00Z",
      "alarm_type": "vehicle"
    },
    {
      "alarm_id": "ALM-API-2",
      "camera_id": "CAM-API-1",
      "timestamp": "2026-06-20T12:01:00Z",
      "alarm_type": "motion"
    }
  ]'
```

```bash
curl "http://localhost:8000/cameras/CAM-API-1/recent?limit=3"
```

Expected recent-event order:

```text
ALM-API-1
ALM-API-2
ALM-API-3
```

## What I Would Do With More Time

The current implementation focuses on the required ingestion flow, Postgres persistence, Redis recent-event caching, and basic tests. With more time, I would harden it in the following areas:

- Add Alembic migrations instead of startup schema creation, so schema changes are explicit, reviewed, and safe to apply during deployment.
- Add structured JSON logging with request IDs, route names, status codes, and request durations.
- Add API metrics for request volume, error rate, and latency percentiles.
- Add query latency monitoring around Postgres calls, including timing for inserts, bulk inserts, and recent-event lookups.
- Enable `pg_stat_statements` in Postgres to identify slow or frequently executed queries.
- Track Redis cache hit/miss rates for the recent-events endpoint.
- Add integration tests that run against real Postgres and Redis in Docker.
- Add authentication and rate limiting for production API exposure.
- Add API versioning, for example `/api/v1/alarms`, to protect future clients from breaking changes.
- Add pagination for larger historical query endpoints.
- Add cache repair or cache invalidation metrics.
- Add deployment configuration for a managed environment such as ECS/Fargate, Cloud Run, Fly.io, Render, or Railway.
- Add readiness checks, secrets management, and separate staging/production environment configuration.