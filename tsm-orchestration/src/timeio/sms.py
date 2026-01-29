import os
import warnings

import psycopg
import logging
import json
import time

from psycopg import sql, Connection, Cursor
from typing import Union, Dict, Optional, Any
from urllib.request import urlopen, Request
from urllib.parse import urljoin
from datetime import datetime, timezone
from functools import reduce
from operator import getitem

from timeio.databases import Database


class SmsCVSyncer:
    def __init__(self, cv_api_url, db_conn_str):
        self.file_names = [
            "sms_cv_measured_quantity.json",
            "sms_cv_license.json",
            "sms_cv_aggregation_type.json",
            "sms_cv_unit.json",
        ]
        self.cv_api_url = cv_api_url
        self.db_conn_str = db_conn_str
        self.db = self.connect()
        self.logger = logging.getLogger("sync_sms_cv")

    def sync(self):
        here = os.path.dirname(os.path.abspath(__file__))
        file_path_list = [
            os.path.join(here, "..", "cv_tables", file_name)
            for file_name in self.file_names
        ]

        with self.db as conn:
            with conn.cursor() as c:
                for file_path in file_path_list:
                    with open(file_path, "r") as f:
                        table_dict = json.load(f)
                    self.create_table(c=c, table_dict=table_dict)
                    self.upsert_table(c=c, url=self.cv_api_url, table_dict=table_dict)

    @staticmethod
    def get_utc_str() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S (UTC)")

    def connect(self, retries: int = 4, sleep: int = 3) -> Connection:
        err = None
        for _ in range(retries):
            try:
                return psycopg.connect(self.db_conn_str)
            except Exception as e:
                err = e
                self.logger.debug(f"{self.get_utc_str()}: Retrying...")
                time.sleep(sleep)
        raise ConnectionError(f"Could not connect to database") from err

    def get_data_from_url(
        self, url: str, endpoint: str, token: Optional[str] = None
    ) -> Dict:
        target = urljoin(url, endpoint)
        self.logger.info(f"{self.get_utc_str()}: Getting data from {target}")
        all_data = []
        headers = {}
        if token:
            headers["X-APIKEY"] = token
        while True:
            request = Request(target, headers=headers)
            response = urlopen(request)
            data = json.loads(response.read())
            all_data.extend(data["data"])
            target = data.get("links", {}).get("next", None)
            if target is None:
                break
        return all_data

    @staticmethod
    def _remove_id_duplicates(data: list[dict]) -> list[dict]:
        seen = set()
        uniq = []
        for item in data:
            if item["id"] not in seen:
                uniq.append(item)
                seen.add(item["id"])
        return uniq

    @staticmethod
    def _value_from_dict(dict_: dict, path: list) -> Union[str, int, float, bool, None]:
        """Extracts a value from a nested dict by a path of keys.
        Example:
            >>> data = {"a": {"b": 99}, "c": 42}
            >>> SmsCVSyncer._value_from_dict(data, ["c"])
            42
            >>> SmsCVSyncer._value_from_dict(data, ["a", "b"])
            99
        """
        return reduce(getitem, path, dict_)  # type: ignore

    @staticmethod
    def _to_postgres_str(val: Union[str, int, float, bool, None]) -> str:
        warnings.warn(
            "Deprecated method use sql.Literal and SmsCVSyncer.convert_special instead",
            DeprecationWarning,
        )
        if val is None:
            return "NULL"  # in postgres None is NULL
        if type(val) == bool:
            return f"{val}"
        if type(val) == int:
            return f"{val}"
        if type(val) == float:
            return f"{val}"
        if type(val) == str:
            try:
                # try to convert string to int
                # some integer keys are provided as string by the api
                # and need to be converted to int for postgres
                return f"{int(val)}"
            except (ValueError, TypeError):
                # replace single quotes with double single quotes
                # to escape single quote string termination in postgres
                val = val.replace("'", "''")
                # return string in single quotes
                # to mark it as a string for postgres
                return f"'{val}'"
        else:
            raise TypeError(f"Unconvertible type {type(val).__qualname__}")

    @staticmethod
    def convert_special(value):
        # some integers are send as strings
        if isinstance(value, str) and str.isnumeric(value):
            value = int(value)
        return value

    @staticmethod
    def _table_is_foreign(c: Cursor, table_name: str) -> bool:
        query = sql.SQL(
            "SELECT table_type FROM information_schema.tables WHERE table_name=%s"
        )
        c.execute(query, (table_name,))
        r = c.fetchone()
        return r is not None and r[0] == "FOREIGN"

    def _drop_foreign_table(self, c: Cursor, table_name: str) -> None:
        query = sql.SQL("DROP FOREIGN TABLE IF EXISTS {table}").format(
            table=sql.Identifier(table_name)
        )
        if self._table_is_foreign(c=c, table_name=table_name):
            try:
                c.execute(query)
            except Exception as e:
                self.logger.error(f"Could not drop foreign table {table_name}:\n{e}")

    @staticmethod
    def _table_create_query(table_dict: dict) -> sql.Composed:
        # e.g. CREATE TABLE IF NOT EXISTS foo (c1 BIGINT, c2 VARCHAR(200), ... )"
        template = sql.SQL("CREATE TABLE IF NOT EXISTS {table} ({columns})")

        table = sql.Identifier(table_dict["name"])
        columns = [
            sql.SQL("{col} {type}").format(
                col=sql.Identifier(k),
                type=sql.SQL(v["type"]),
            )
            for k, v in table_dict["keys"].items()
        ]
        return template.format(table=table, columns=sql.SQL(", ").join(columns))

    def create_table(self, c: Cursor, table_dict: Dict) -> None:
        """
        creates table based on table_dict (loaded from foo-table.json in ./tables)

        e.g.:
        CREATE TABLE IF NOT EXISTS foo-table (
            id integer primary key,
            column_b varchar(255),
            column_c text,
            ...
        )
        """
        self._drop_foreign_table(c=c, table_name=table_dict["name"])
        create_query = self._table_create_query(table_dict)
        c.execute(create_query)

    def _table_upsert_query(self, table_dict: dict, data: list[dict]) -> sql.Composed:

        if "keys" not in table_dict.keys():
            raise KeyError("Missing mandatory top-level field 'keys'")
        if "name" not in table_dict.keys():
            raise KeyError("Missing mandatory top-level field 'name'")
        if "id" not in table_dict["keys"].keys():
            raise KeyError("Missing mandatory field 'id' in 'keys'")

        template = sql.SQL(
            "INSERT INTO {table} ({columns}) VALUES {values} ON CONFLICT (id) DO UPDATE SET {excludeds}",
        )
        columns = [key for key in table_dict["keys"]]

        value_tuples = []
        for item in data:  # type: dict
            values = []
            for key, val in table_dict["keys"].items():
                value = self._value_from_dict(item, val["path"])
                value = self.convert_special(value)
                values.append(value)

            # create a tuple e.g. ('val' 'val2' 99)
            tup = sql.SQL("({})").format(sql.SQL(", ").join(map(sql.Literal, values)))
            value_tuples.append(tup)

        return template.format(
            table=sql.Identifier(table_dict["name"]),
            columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
            values=sql.SQL(", ").join(value_tuples),
            excludeds=sql.SQL(", ").join(
                sql.SQL("{c} = EXCLUDED.{c}").format(c=sql.Identifier(c))
                for c in columns
                if c != "id"
            ),
        )

    def upsert_table(
        self, c: Cursor, url: str, table_dict: dict, token: Optional[str] = None
    ) -> None:
        """
        updates table based on table_dict (loaded from foo-table.json in ./tables)
        with data queried from target

        query is built by _table_upsert_query()

        e.g.:
        INSERT INTO TABLE foo-table
            (id, column_b, column_c, ...)
        VALUES
            (1, 'foo', 'bar', ...),
            (2, 'foot', 'bard', ...),
            ...
        ON CONFLICT (id) DO UPDATE SET
            column_b = EXCLUDED.column_b,
            column_c = EXCLUDED.column_c,
            ...
        """
        name = table_dict["name"]
        endpoint = table_dict["endpoint"]
        data = self.get_data_from_url(url=url, endpoint=endpoint, token=token)
        data = self._remove_id_duplicates(data)
        query = self._table_upsert_query(table_dict, data)

        try:
            c.execute(query)
            self.logger.info(f"Data successfully synced to table {name}")
        except psycopg.Error as e:
            self.logger.error(f"Could not sync data to table {name}:\n{e}")
            raise e


class SmsMaterializedViewsSyncer:
    def __init__(self, db_conn_str):
        self.db = Database(db_conn_str)
        self.materialized_views = []
        self.logger = logging.getLogger("sync_sms_views")

    def collect_materialized_views(self):
        # Get a list of materialized views with the prefix "sms_"
        query = (
            "SELECT matviewname FROM pg_matviews WHERE "
            "schemaname = 'public' AND matviewname LIKE 'sms_%' "
        )
        try:
            with self.db.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    tuples = cur.fetchall()
                    self.materialized_views = [tup[0] for tup in tuples]
                    return self

        except psycopg.Error as e:
            self.logger.error(
                f"Error occurred during fetching materialized views: {e!r}"
            )

    def update_materialized_views(self) -> None:
        template = sql.SQL("REFRESH MATERIALIZED VIEW CONCURRENTLY {}")
        try:
            with self.db.connection() as conn:
                with conn.cursor() as cur:
                    for view in self.materialized_views:
                        cur.execute(template.format(sql.Identifier(view)))
                        self.logger.info(f"Refreshed materialized view: {view}")
        except psycopg.Error as e:
            self.logger.error(
                f"Error occurred during refreshing materialized view: {e!r}"
            )
