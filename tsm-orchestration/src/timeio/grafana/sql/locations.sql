SELECT
  l."LOCATION"::json->'coordinates'->0 AS "Longitude",
  l."LOCATION"::json->'coordinates'->1 AS "Latitude",
  t."NAME" AS "ThingName",
  STRING_AGG(DISTINCT s."NAME", ', ') AS "SensorNames",
  STRING_AGG(DISTINCT p."NAME", ', ') AS "PropertyNames"
FROM "LOCATIONS" l
JOIN "THINGS_LOCATIONS" tl ON l."ID" = tl."LOCATION_ID"
JOIN "THINGS" t ON t."ID" = tl."THING_ID"
JOIN "DATASTREAMS" d ON d."THING_ID" = t."ID"
JOIN "SENSORS" s ON s."ID" = d."SENSOR_ID"
JOIN "OBS_PROPERTIES" p ON d."OBS_PROPERTY_ID" = p."ID"
GROUP BY l."LOCATION", t."NAME"