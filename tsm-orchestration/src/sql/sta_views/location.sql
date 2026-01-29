DROP VIEW IF EXISTS "LOCATIONS" CASCADE;
CREATE VIEW "LOCATIONS" AS
SELECT
    id AS "ID",
    name AS "NAME",
    'Location of ' || name AS "DESCRIPTION",
    'application/vnd.geo+json'::varchar AS "ENCODING_TYPE",
    -- Return JSONB directly for Grafana compatibility (l."LOCATION"::json cast requires it)
    COALESCE(properties->'location', '{"type": "Point", "coordinates": [0,0]}'::jsonb) AS "LOCATION",
    CASE 
        WHEN jsonb_typeof(properties) = 'object' THEN properties
        WHEN properties IS NULL THEN '{}'::jsonb
        ELSE jsonb_build_object('wrapped_value', properties)
    END AS "PROPERTIES",
    ST_GeomFromGeoJSON(COALESCE(properties->'location', '{"type": "Point", "coordinates": [0,0]}'::jsonb)) AS "GEOM"
FROM thing;
