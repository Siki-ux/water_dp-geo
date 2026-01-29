-- Using "result_quality -> -1 ->>" because result_quality is an array of quality objects
-- we use "-1" to always select the last one
SELECT o.result_time AS "time",
1 AS "quality_flag",
jsonb_build_object(
    'annotation', CAST ((result_quality -> -1 ->> 'annotation') AS DECIMAL),
    'measure', result_quality -> -1 ->> 'properties', 'measure',
    'user_label', result_quality -> -1 ->> 'properties', 'userLabel'
) AS "qaqc_result"
FROM observation o
WHERE o.datastream_id = (
    SELECT dp.ds_id
    FROM datastream_properties dp
    WHERE ${{datastream_pos:singlequote}} in (dp.property,dp.position)
    AND dp.t_uuid::text = '{uuid}'
) AND ${{show_qaqc_flags}} = 'True'
AND result_quality IS NOT NULL
AND result_quality <> 'null'
AND (result_quality -> -1 ->> 'annotation') IS NOT NULL
AND (result_quality -> -1 ->> 'annotation') <> '0.0'
AND (result_quality -> -1 ->> 'annotation') <> '-inf'
ORDER BY o.result_time ASC