from psycopg import connect, sql
import yaml


class DatastreamComparer:
    def __init__(self, dsn: str, schema: str, mapping_file: str):
        self.dsn = dsn
        self.schema = schema
        self.mapping_file = mapping_file
        self.mapping = self._read_yaml()
        self.thing_uuid = next(iter(self.mapping))

        self.query_ds_id = sql.SQL(
            """
            SELECT d.id, d.name, d.position FROM {schema}.datastream d
            JOIN {schema}.thing t ON t.id = d.thing_id
            WHERE t.uuid = %s AND d.position = %s
        """
        ).format(schema=sql.Identifier(self.schema))

        self.query_timerange = sql.SQL(
            """
            SELECT MIN(result_time), MAX(result_time)
            FROM {schema}.observation
            WHERE datastream_id = %s
        """
        ).format(schema=sql.Identifier(self.schema))

        self.query_timerange_obs = sql.SQL(
            """
            SELECT result_time, result_type, result_number,
                   result_string, result_json, result_boolean
            FROM {schema}.observation
            WHERE datastream_id = %s
              AND result_time BETWEEN %s AND %s
        """
        ).format(schema=sql.Identifier(self.schema))

    def _read_yaml(self):
        with open(self.mapping_file, "r") as f:
            return yaml.safe_load(f)

    def get_datastream_info(self, pos: str):
        with connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    self.query_ds_id,
                    (
                        self.thing_uuid,
                        pos,
                    ),
                )
                row = cur.fetchone()
        return row

    def get_header_timerange(self, ds_id):
        with connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(self.query_timerange, (ds_id,))
                row = cur.fetchone()
        return row[0], row[1]

    def get_timerange_obs(self, ds_id, ts_from, ts_to):
        with connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    self.query_timerange_obs,
                    (
                        ds_id,
                        ts_from,
                        ts_to,
                    ),
                )
                rows = cur.fetchall()
        return rows

    def compare_datastreams(self):
        mapping = self.mapping.get(self.thing_uuid)
        if not mapping:
            raise ValueError(f"No mapping found for thing: {self.thing_uuid}")
        results = list()
        for k, v in mapping.items():
            ds_position = self.get_datastream_info(str(k))
            ds_header = self.get_datastream_info(v)
            ts_from, ts_to = self.get_header_timerange(ds_header[0])
            obs_pos = self.get_timerange_obs(ds_position[0], ts_from, ts_to)
            obs_header = self.get_timerange_obs(ds_header[0], ts_from, ts_to)
            equal = sorted(obs_pos) == sorted(obs_header)
            results.append(
                {
                    "ds_position_id": ds_position[0],
                    "ds_position_name": ds_position[1],
                    "ds_position_pos": ds_position[2],
                    "ds_header_id": ds_header[0],
                    "ds_header_name": ds_header[1],
                    "ds_header_pos": ds_header[2],
                    "equal": equal,
                }
            )
        return {
            "thing_uuid": self.thing_uuid,
            "compare": results,
        }
