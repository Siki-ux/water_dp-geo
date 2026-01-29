DROP VIEW IF EXISTS "OBSERVATIONS" CASCADE;
CREATE VIEW "OBSERVATIONS" AS
SELECT
    id AS "ID",
    result_time AS "PHENOMENON_TIME_START",
    result_time AS "PHENOMENON_TIME_END",
    result_time AS "RESULT_TIME",
    result_type AS "RESULT_TYPE",
    result_number AS "RESULT_NUMBER",
    result_string AS "RESULT_STRING",
    result_boolean AS "RESULT_BOOLEAN",
    result_json AS "RESULT_JSON",
    result_latitude AS "RESULT_LATITUDE",
    result_longitude AS "RESULT_LONGITUDE",
    result_altitude AS "RESULT_ALTITUDE",
    result_quality AS "RESULT_QUALITY",
    parameters AS "PARAMETERS",
    datastream_id AS "DATASTREAM_ID",
    NULL::bigint AS "FEATURE_ID",
    valid_time_start AS "VALID_TIME_START",
    valid_time_end AS "VALID_TIME_END",
    jsonb_build_object() AS "PROPERTIES"
FROM observation;
