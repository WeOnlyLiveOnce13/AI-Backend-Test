# Task 2 — SQL (~1.5 hours)

> SQL is weighted heavily in this exercise. Target dialect: **PostgreSQL 14+**.

## Setup

Use whichever of the two options below is easier for you. Then load the schema and seed.

### Option A — Docker

```bash
docker run --name takehome-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16
```

### Option B — Local Postgres (no Docker)

Install and start a native PostgreSQL 14+ server, then create a database for the task.

**macOS (Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16        # starts the server now and on login
createdb takehome                          # uses your OS user as a superuser role
```

**Ubuntu / Debian:**
```bash
sudo apt-get update && sudo apt-get install -y postgresql
sudo systemctl start postgresql            # or: sudo service postgresql start
sudo -u postgres createdb takehome
sudo -u postgres createuser --superuser "$USER"   # let your shell user connect
```

**Windows:** install via the EnterpriseDB installer (or `winget install PostgreSQL.PostgreSQL`),
which starts the service automatically, then from the SQL Shell / PowerShell:
```powershell
createdb -U postgres takehome
```

This gives you a connection string like `postgresql:///takehome` (local socket) or
`postgresql://postgres:postgres@localhost:5432/takehome`.

### Load schema + seed (either option)

```bash
# Docker default db is "postgres"; local install above uses "takehome".
psql postgresql://postgres:postgres@localhost:5432/postgres -f schema/schema.sql
psql postgresql://postgres:postgres@localhost:5432/postgres -f seed/seed.sql

# For the local (no-Docker) setup, e.g.:
# psql takehome -f schema/schema.sql
# psql takehome -f seed/seed.sql
```

Sanity check the load: `psql <conn> -c "SELECT count(*) FROM alarms;"` should return ~55k.

(If you prefer SQLite or DuckDB, note any dialect changes you made — but Postgres is
what we'll run your answers against.)

## Schema (provided)

Five tables in `schema/schema.sql`, populated with ~100k rows by `seed/seed.sql`:

- **`sites`** — physical locations / customers.
- **`cameras`** — cameras, each belonging to a site.
- **`alarms`** — raw alarms (camera, timestamp, type).
- **`dispositions`** — operator outcome per alarm (e.g. `true_alarm`, `false_alarm`,
  `dispatched`) with dispatch timing.
- **`model_predictions`** — model output per alarm (class, confidence).

See `schema/schema.sql` for exact columns and keys.

## Questions

Put each query in its own file under `queries/` (suggested names in brackets). Put the
prose answers (5 and 6) in this README.

1. **Warm-up** (`q1_top_sites.sql`) — top *N* sites by alarm volume in a given date range.
2. **Window functions** (`q2_rolling_false_alarm_rate.sql`) — 7-day rolling false-alarm
   rate per camera; flag cameras with a week-over-week change > 50%.
3. **Percentiles** (`q3_dispatch_percentiles.sql`) — P50 and P95 operator dispatch time
   per customer.
4. **Anti-join** (`q4_predictions_no_events.sql`) — cameras that produced predictions but
   had zero confirmed events in the last 14 days.
5. **Schema design** (prose, ≈1 page) — brief: *"store dispositions, support fast lookups
   by camera and time window, 2-year retention."* Propose schema + indexes + partitioning,
   and justify.
6. **Optimisation** (prose + `queries/q6_optimised.sql`) — see `optimisation/`. Rewrite the
   slow query and explain the speedup with reference to the plan.

## What we're assessing

Correct results, idiomatic CTEs and window functions, schema-design judgement, and the
ability to read an `EXPLAIN ANALYZE` plan and act on it.
