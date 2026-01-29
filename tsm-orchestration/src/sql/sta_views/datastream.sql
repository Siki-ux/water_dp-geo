DROP VIEW IF EXISTS "DATASTREAMS" CASCADE;
CREATE VIEW "DATASTREAMS" AS
SELECT
    tsm_ds.id AS "ID",
    tsm_ds.name AS "NAME",
    tsm_ds.description AS "DESCRIPTION",
    tsm_ds.thing_id AS "THING_ID",
    1::bigint AS "SENSOR_ID",
    1::bigint AS "OBS_PROPERTY_ID",
    COALESCE(tsm_ds.properties->'unitOfMeasurement', jsonb_build_object(
        'symbol', COALESCE(dp.unit_uri, '?'), 
        'name', COALESCE(dp.unit_name, 'Unknown'), 
        'definition', COALESCE(dp.property_uri, 'http://unknown')
    )) AS "UNIT_OF_MEASUREMENT",
    COALESCE(dp.unit_name, 'Unknown') AS "UNIT_NAME",
    COALESCE(dp.unit_uri, '?') AS "UNIT_SYMBOL",
    COALESCE(dp.property_uri, 'http://unknown') AS "UNIT_DEFINITION",
    CASE 
        WHEN tsm_ds.name = 'journal' THEN 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Observation'
        ELSE COALESCE(tsm_ds.properties->>'observationType', 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement')
    END AS "OBSERVATION_TYPE",
    NULL::geometry AS "OBSERVED_AREA",
    NULL::timestamp AS "PHENOMENON_TIME_START",
    NULL::timestamp AS "PHENOMENON_TIME_END",
    NULL::timestamp AS "RESULT_TIME_START",
    NULL::timestamp AS "RESULT_TIME_END",
    CASE 
        WHEN jsonb_typeof(tsm_ds.properties) = 'object' THEN tsm_ds.properties
        WHEN tsm_ds.properties IS NULL THEN '{}'::jsonb
        ELSE jsonb_build_object('wrapped_value', tsm_ds.properties)
    END AS "PROPERTIES"
FROM datastream tsm_ds
JOIN thing tsm_t ON tsm_ds.thing_id = tsm_t.id
LEFT JOIN public.sms_datastream_link sdl ON tsm_t.uuid = sdl.thing_id AND tsm_ds.name = sdl.datastream_name
LEFT JOIN public.sms_device_property dp ON sdl.device_property_id = dp.id;


