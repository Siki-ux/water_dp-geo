-- Get last result time by schema
CREATE FUNCTION ${monitoring_db_user}.get_latest_observation_all_schemas()
RETURNS TABLE(schema_name text, result_time timestamptz)
LANGUAGE plpgsql STABLE SECURITY DEFINER AS $$
DECLARE
  sch text;
  qry text;
BEGIN
  FOR sch IN
    SELECT table_schema
    FROM information_schema.tables
    WHERE table_name = 'observation'
  LOOP
    qry := format(
      'SELECT %L::text AS schema_name,
              o.result_time::timestamptz AS result_time
       FROM %I.observation o
       ORDER BY o.id DESC
       LIMIT 1',
      sch, sch
    );
    RETURN QUERY EXECUTE qry;
  END LOOP;
END;
$$;

-- Get last result time by ingest type for a given schema, limited to a time interval
CREATE OR REPLACE FUNCTION ${monitoring_db_user}.get_latest_observation_by_ingest_type_for_schema(
  p_schema text,
  p_interval interval DEFAULT '24 hours'
)
RETURNS TABLE (ingest_type text, last_result_time timestamptz)
LANGUAGE plpgsql
STABLE SECURITY DEFINER
AS $$
DECLARE
  sql_text text;
BEGIN
  sql_text := format($f$
    SELECT
      (CASE
        WHEN cit.name = 'extapi' THEN COALESCE(ceat.name, 'extapi')
        ELSE cit.name
      END)::text AS ingest_type,
      MAX(o.result_time) AS last_result_time
    FROM config_db.thing ct
    JOIN %I.thing t ON ct.uuid = t.uuid
    JOIN %I.datastream ds ON t.id = ds.thing_id
    JOIN config_db.ingest_type cit ON ct.ingest_type_id = cit.id
    LEFT JOIN config_db.ext_api cea ON ct.ext_api_id = cea.id
    LEFT JOIN config_db.ext_api_type ceat ON cea.api_type_id = ceat.id
    JOIN %I.observation o ON ds.id = o.datastream_id
    WHERE o.result_time >= NOW() - $1
      AND o.result_time IS NOT NULL
    GROUP BY ingest_type
    ORDER BY ingest_type
  $f$, p_schema, p_schema, p_schema);

  RETURN QUERY EXECUTE sql_text USING p_interval;
END;
$$;

-- Loop over all schemas and get last result time by ingest type, limited to a time interval
CREATE OR REPLACE FUNCTION ${monitoring_db_user}.get_latest_observation_by_ingest_type_all_schemas(
  p_interval interval DEFAULT '24 hours'
)
RETURNS TABLE (schema_name text, ingest_type text, last_result_time timestamptz)
LANGUAGE plpgsql
STABLE SECURITY DEFINER
AS $$
DECLARE
  sch RECORD;
  sql_text text;
BEGIN
  FOR sch IN
    SELECT table_schema
    FROM information_schema.tables
    WHERE table_name = 'observation'

  LOOP
    sql_text := format(
      'SELECT %L::text AS schema_name, ingest_type, last_result_time
       FROM ${monitoring_db_user}.get_latest_observation_by_ingest_type_for_schema(%L, $1)',
      sch.table_schema,
      sch.table_schema
    );
    RETURN QUERY EXECUTE sql_text USING p_interval;
  END LOOP;
END;
$$;