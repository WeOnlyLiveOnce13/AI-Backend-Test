# Task 3, Option B — FastAPI alarm ingestion service

Build a small but production-minded service that ingests alarm events.

## Requirements

1. **Persist** incoming alarm events to **Postgres**.
2. **Cache** the latest *N* events per camera in **Redis**. Make *N* a configurable
   environment variable (e.g. `RECENT_CACHE_SIZE`). You may assume the read endpoint's
   `limit` will not exceed *N* for a cache hit — see the next point for how to handle
   `limit > N`.
3. Expose at least these endpoints:
   - `POST /alarms` — ingest a single alarm event.
   - `POST /alarms/bulk` — bulk ingest (the body may contain hundreds of events).
   - `GET /cameras/{camera_id}/recent?limit=K` — the K most recent events for a camera.
     Serve from the Redis cache when it can satisfy the request; **define and document
     your fallback when `limit` exceeds what the cache holds** (e.g. fall back to Postgres
     for the full result). State the behaviour you chose and why.
4. Ship a **`Dockerfile`** and a **`docker-compose.yml`** that brings up the app +
   Postgres + Redis with one command.
5. Include **basic tests** (the happy path plus at least one failure/validation case).

> **Ordering caveat (carries over from Task 1):** alarm timestamps can arrive **out of
> order**, including via bulk ingest. "Recent events" must be returned in correct
> chronological order regardless of arrival order — choose your cache representation
> accordingly.

## Suggested alarm event shape

```json
{
  "alarm_id": "string",
  "camera_id": "string",
  "timestamp": "2026-06-20T12:00:00Z",
  "alarm_type": "person",
  "metadata": { "confidence": 0.91 }
}
```

You may adjust the shape — document any changes. This is an **extended version of the
Task 1 data** (`alarm_id, timestamp, camera_id, alarm_type`) with an added optional
`metadata` object; map `metadata` to a **JSONB** column in Postgres. If you seed from the
Task 1 `alarms.csv`, treat `metadata` as absent/null for those rows.

## What we're assessing

API design and validation, sensible persistence + caching boundaries, configuration via
environment, error handling, and that it actually runs from `docker compose up`. We also
look at **how you handle network overhead during bulk operations** — efficient
batching/pipelining of writes to Postgres and Redis rather than a round-trip per event.

## Provided scaffold

A minimal `app/` package and `pyproject`/`requirements` starter is included so you can
focus on the design rather than boilerplate. Extend it however you see fit.
