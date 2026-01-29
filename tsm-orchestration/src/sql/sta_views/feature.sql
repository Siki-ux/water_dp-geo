DROP VIEW IF EXISTS "FEATURES" CASCADE;
CREATE VIEW "FEATURES" AS
SELECT
    1::bigint AS "ID",
    'Default Feature'::varchar AS "NAME",
    'Default Feature'::text AS "DESCRIPTION",
    'application/vnd.geo+json'::varchar AS "ENCODING_TYPE",
    public.ST_GeomFromText('POINT(0 0)') AS "FEATURE",
    NULL::jsonb AS "PROPERTIES";
