# A little exercise on solving take home challenges

Submission for an AI Backend Engineer challenge.

This repository contains four backend-focused tasks:

- Task 1: alarm event grouping
- Task 2: SQL queries, schema design, and optimization
- Task 3: FastAPI alarm ingestion service
- Task 4: Python optimization

The project uses one root `uv` Python project and Docker Compose for infrastructure services.

## Report

The polished report is available here:

[AI Backend Engineer Challenge Report](https://weonlyliveonce13.github.io/AI-Backend-Test/report/)

## Prerequisites

Install:

- Python 3.11+
- `uv`
- Docker Desktop
- Quarto CLI, only if you want to render the report

## Setup

Clone the repository, then from the project root run:

```bash
uv sync
cp .env.example .env
```

The alarm CSV is intentionally not committed to Git. Copy the provided take-home CSV to:

```text
data/alarms.csv
```

The `data/` folder is ignored except for `data/.gitkeep`.

## Quick Check

Run the test suite:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check .
```

## Start Infrastructure

Start Postgres and Redis:

```bash
docker compose up -d postgres redis
```

Check the Compose configuration:

```bash
docker compose config
```

## Task 1: Alarm Event Grouping

Run the event grouping script:

```bash
uv run python tasks/task1_algorithmic/group_alarms.py --input data/alarms.csv
```

The script writes generated outputs to:

```text
tasks/task1_algorithmic/output/events.csv
tasks/task1_algorithmic/output/anomalous_cameras.csv
```

These runtime outputs are ignored by Git.

## Task 2: SQL

Load the schema and seed data into Postgres:

```bash
docker compose exec postgres psql -U postgres -d deepalert -f /sql/schema/schema.sql
docker compose exec postgres psql -U postgres -d deepalert -f /sql/seed/seed.sql
```

Sanity check the loaded data:

```bash
docker compose exec postgres psql -U postgres -d deepalert -c "SELECT count(*) FROM alarms;"
```

Run individual SQL answers:

```bash
docker compose exec postgres psql -U postgres -d deepalert -f /sql/queries/q1_top_sites.sql
docker compose exec postgres psql -U postgres -d deepalert -f /sql/queries/q2_rolling_false_alarm_rate.sql
docker compose exec postgres psql -U postgres -d deepalert -f /sql/queries/q3_dispatch_percentiles.sql
docker compose exec postgres psql -U postgres -d deepalert -f /sql/queries/q4_predictions_no_events.sql
docker compose exec postgres psql -U postgres -d deepalert -f /sql/queries/q6_optimised.sql
```

The schema-design and optimization writeups are in:

```text
tasks/task2_sql/Q5_schema.md
tasks/task2_sql/Q6_explanation.md
```

## Task 3: FastAPI Ingestion Service

Run the API with Docker Compose:

```bash
docker compose --profile app up --build
```

The API is available at:

```text
http://localhost:8000
```

Interactive API docs are available at:

```text
http://localhost:8000/docs
```

Health check:

```bash
curl http://localhost:8000/health
```

Ingest one alarm:

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

Ingest alarms in bulk:

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

Fetch recent events for a camera:

```bash
curl "http://localhost:8000/cameras/CAM-API-1/recent?limit=3"
```

Run Task 3 tests:

```bash
uv run pytest tasks/task3_python/option_b_fastapi_ingestion/tests
```

## Task 4: Python Optimization

Run the optimized implementation:

```bash
uv run python tasks/task4_optimization/optimized.py --csv data/alarms.csv
```

Run a smaller comparison:

```bash
uv run python tasks/task4_optimization/slow_code.py --limit 4000 --csv data/alarms.csv
uv run python tasks/task4_optimization/optimized.py --limit 4000 --csv data/alarms.csv
```

Measurements are documented in:

```text
tasks/task4_optimization/measurements.md
```

## Render the Quarto Report

Render the report:

```bash
quarto render
```

The rendered HTML is created at:

```text
docs/report/index.html
```

## Optional Tools

Start pgAdmin:

```bash
docker compose --profile tools up -d pgadmin
```

Open:

```text
http://localhost:5050
```

Default credentials are defined in `.env.example`.

## Final Verification

Before submitting, run:

```bash
uv run pytest
uv run ruff check .
docker compose config
docker compose --profile app config
quarto render
```

## Notes

- `.env` is local and ignored by Git.
- `data/alarms.csv` is local and ignored by Git.
- Task runtime outputs are ignored by Git.
- Postgres and Redis are provided through Docker Compose.
- The API uses Postgres as the source of truth and Redis as a recent-events cache.