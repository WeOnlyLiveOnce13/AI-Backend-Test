-- Task 2, Q6: this query is SLOW. Rewrite it to be faster and explain why,
-- referencing the EXPLAIN ANALYZE plan in explain_analyze.txt.
--
-- Goal: per camera, how many alarms fired and how many were false alarms
-- in the 14 days up to 2026-06-21, busiest first.

SELECT
    c.camera_id,
    c.camera_name,
    (SELECT count(*)
       FROM alarms a
      WHERE a.camera_id = c.camera_id
        AND a.alarm_ts::date >= DATE '2026-06-07') AS recent_alarms,
    (SELECT count(*)
       FROM dispositions d
       JOIN alarms a2 ON a2.alarm_id = d.alarm_id
      WHERE a2.camera_id = c.camera_id
        AND d.outcome = 'false_alarm'
        AND a2.alarm_ts::date >= DATE '2026-06-07') AS recent_false_alarms
FROM cameras c
ORDER BY recent_false_alarms DESC, recent_alarms DESC;
