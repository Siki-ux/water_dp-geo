WITH date_filtered AS (
-- This query returns the data chosen by the datepicker, or
-- returns null if no data is in the selected date range.
  SELECT
    o.result_time AS "time",
    o.result_number AS "value"
  FROM observation o
  WHERE $__timeFilter(o.result_time)
  AND o.datastream_id = (
      SELECT dp.ds_id FROM datastream_properties dp
      WHERE ${{datastream_pos:singlequote}} in (dp.property, dp.position)
      AND dp.t_uuid :: text = '{uuid}')
  ORDER BY o.result_time DESC
  LIMIT 1000000  -- 1M
),
fallback AS (
-- This query returns the most recent 10k datapoints
  SELECT
    o.result_time AS "time",
    o.result_number AS "value"
  FROM observation o
  WHERE o.datastream_id = (
    SELECT dp.ds_id FROM datastream_properties dp
    WHERE ${{datastream_pos:singlequote}} in (dp.property, dp.position)
    AND dp.t_uuid :: text = '{uuid}')
  ORDER BY o.result_time DESC  -- most recent
  LIMIT 10000  -- 10k
)
-- First the date_filtered query is executed. If it returns
-- null, because the user selected a time range without any
-- data, the fallback query is executed and return the most
-- recent 10k data points. This fallback data is not shown
-- immediately, because it is also not the selected timerange,
-- but grafana will now show a ZoomToData button. If the user
-- press the button, the panel will jump to the data from the
-- fallback query (the most recent 10k data points).
SELECT * FROM date_filtered
UNION ALL
SELECT * FROM fallback
WHERE NOT EXISTS (SELECT 1 FROM date_filtered)
ORDER BY "time" ASC