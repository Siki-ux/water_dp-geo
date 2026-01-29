DROP VIEW IF EXISTS "OBS_PROPERTIES" CASCADE;
CREATE VIEW "OBS_PROPERTIES" AS
SELECT
    1::bigint AS "ID",
    'TimeIO Property'::varchar AS "NAME",
    'http://example.org/def'::varchar AS "DEFINITION",
    'Default Property'::text AS "DESCRIPTION",
    NULL::jsonb AS "PROPERTIES";
