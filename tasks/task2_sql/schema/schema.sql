-- DeepAlert take-home: Task 2 schema (PostgreSQL 14+)
-- Indexes here are deliberately minimal. Improving them is part of the exercise.

DROP TABLE IF EXISTS model_predictions CASCADE;
DROP TABLE IF EXISTS dispositions CASCADE;
DROP TABLE IF EXISTS alarms CASCADE;
DROP TABLE IF EXISTS cameras CASCADE;
DROP TABLE IF EXISTS sites CASCADE;

CREATE TABLE sites (
    site_id        INTEGER PRIMARY KEY,
    customer_id    INTEGER NOT NULL,
    customer_name  TEXT    NOT NULL,
    site_name      TEXT    NOT NULL,
    region         TEXT    NOT NULL,
    timezone       TEXT    NOT NULL
);

CREATE TABLE cameras (
    camera_id      INTEGER PRIMARY KEY,
    site_id        INTEGER NOT NULL REFERENCES sites(site_id),
    camera_name    TEXT    NOT NULL,
    status         TEXT    NOT NULL,           -- active | inactive
    installed_at   DATE    NOT NULL
);

CREATE TABLE alarms (
    alarm_id       BIGINT  PRIMARY KEY,
    camera_id      INTEGER NOT NULL REFERENCES cameras(camera_id),
    alarm_ts       TIMESTAMPTZ NOT NULL,
    alarm_type     TEXT    NOT NULL
);

CREATE TABLE dispositions (
    disposition_id   BIGINT PRIMARY KEY,
    alarm_id         BIGINT NOT NULL UNIQUE REFERENCES alarms(alarm_id),
    outcome          TEXT   NOT NULL,          -- false_alarm | true_alarm | ignored
    operator_id      INTEGER NOT NULL,
    acknowledged_at  TIMESTAMPTZ NOT NULL,
    dispatched_at    TIMESTAMPTZ              -- NULL unless a guard was dispatched
);

CREATE TABLE model_predictions (
    prediction_id    BIGINT PRIMARY KEY,
    alarm_id         BIGINT NOT NULL REFERENCES alarms(alarm_id),
    predicted_class  TEXT   NOT NULL,
    confidence       NUMERIC(4,3) NOT NULL,
    model_version    TEXT   NOT NULL,
    predicted_at     TIMESTAMPTZ NOT NULL
);

-- Minimal supporting index only. (No index on any *_ts column on purpose.)
CREATE INDEX idx_alarms_camera_id ON alarms(camera_id);
