SET search_path TO config_db;

CREATE TABLE file_parser_backup AS TABLE file_parser WITH DATA;

UPDATE file_parser
   SET params = jsonb_set(
     params,
     '{timestamp_columns}',
     COALESCE(
       params->'timestamp_columns',
       jsonb_build_array(
         jsonb_build_object(
           'column', (params->>'timestamp_column')::int,
           'format', params->>'timestamp_format'
         )
       )
     )
   )
 WHERE params ? 'timestamp_column'
   AND params ? 'timestamp_format'
   AND NOT params ? 'timestamp_columns';

UPDATE file_parser
   SET params = params - 'timestamp_column' - 'timestamp_format'
 WHERE params ? 'timestamp_column' OR params ? 'timestamp_format';

