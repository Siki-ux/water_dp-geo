DROP VIEW IF EXISTS "THINGS" CASCADE;
CREATE VIEW "THINGS" AS
SELECT
    id AS "ID",
    description AS "DESCRIPTION",
    name AS "NAME",
    -- Ensure properties is a JSON Map/Object before merging
    CASE 
        WHEN jsonb_typeof(properties) = 'object' THEN properties
        WHEN properties IS NULL THEN '{}'::jsonb
        ELSE jsonb_build_object('wrapped_value', properties)
    END || jsonb_build_object('uuid', uuid) AS "PROPERTIES"
FROM thing;
