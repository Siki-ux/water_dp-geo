SELECT timestamp, level, message, origin
FROM journal
JOIN thing t on journal.thing_id = t.id
WHERE t.uuid::text = '{uuid}'
ORDER BY timestamp DESC