DROP VIEW IF EXISTS "SENSORS" CASCADE;
CREATE VIEW "SENSORS" AS
SELECT
    1::bigint AS "ID",
    'TimeIO Default Sensor'::varchar AS "NAME",
    'Default sensor for TimeIO'::text AS "DESCRIPTION",
    'application/pdf'::varchar AS "ENCODING_TYPE",
    'http://example.org'::varchar AS "METADATA",
    NULL::jsonb AS "PROPERTIES";
