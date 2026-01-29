from __future__ import annotations

import json
import logging
import os

import psycopg
from psycopg import sql

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.databases import Database
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.journaling import Journal
from timeio.crypto import decrypt, get_crypt_key
from timeio.configdb import upsert_schema_thing_mapping

logger = logging.getLogger("db-setup")
journal = Journal("System", errors="ignore")

STA_PREFIX = "sta_"
GRF_PREFIX = "grf_"


class CreateThingInPostgresHandler(AbstractHandler):
    def __init__(self):
        super().__init__(
            topic=get_envvar("TOPIC"),
            mqtt_broker=get_envvar("MQTT_BROKER"),
            mqtt_user=get_envvar("MQTT_USER"),
            mqtt_password=get_envvar("MQTT_PASSWORD"),
            mqtt_client_id=get_envvar("MQTT_CLIENT_ID"),
            mqtt_qos=get_envvar("MQTT_QOS", cast_to=int),
            mqtt_clean_session=get_envvar("MQTT_CLEAN_SESSION", cast_to=bool),
        )
        self.db = Database(get_envvar("DATABASE_URL"))
        self.configdb_dsn = get_envvar("CONFIGDB_DSN")

    def act(self, content: dict, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.configdb_dsn)
        logger.info(f"start processing. {thing.name=}, {thing.uuid=}")
        ro_user = thing.database.ro_username.lower()
        user = thing.database.username.lower()

        # 1. Check, if there is already a database user for this project
        if not self.user_exists(user):
            logger.debug(f"create user {user}")
            self.create_user(thing)

        # 2. Check if schema exists, if not create it and deploy DDL/DML
        schema = thing.database.schema.lower()
        if not self.schema_exists(schema):
            logger.debug(f"create schema {schema}")
            self.create_schema(thing)
            logger.debug("deploy dll")
            self.deploy_ddl(thing)
            logger.debug("deploy dml")
            self.deploy_dml(thing)

        with self.db.connection() as conn:
            upsert_schema_thing_mapping(conn, thing.uuid, thing.database.schema)

        if not self.user_exists(sta_user := STA_PREFIX + ro_user):
            logger.debug(f"create sta read-only user {sta_user}")
            self.create_ro_user(thing, user_prefix=STA_PREFIX)

        if not self.user_exists(grf_user := GRF_PREFIX + ro_user):
            logger.debug(f"create grafana read-only user {grf_user}")
            self.create_ro_user(thing, user_prefix=GRF_PREFIX)

        logger.info("update/create thing in db")
        created = self.upsert_thing(thing)
        journal.info(f"{'Created' if created else 'Updated'} Thing", thing.uuid)

        logger.debug("create/refresh frost views")
        self.create_frost_views(thing)
        logger.debug(f"grand frost view privileges to {sta_user}")
        self.grant_sta_select(thing, user_prefix=STA_PREFIX)
        logger.debug("create/refresh grafana views")
        self.create_grafana_views(thing)
        logger.debug(f"grand grafana view privileges to {grf_user}")
        self.grant_grafana_select(thing, user_prefix=GRF_PREFIX)

    def create_user(self, thing):

        with self.db.connection() as conn:
            with conn.cursor() as c:
                user = sql.Identifier(thing.database.username.lower())
                passw = decrypt(thing.database.password, get_crypt_key())
                c.execute(
                    sql.SQL("CREATE ROLE {user} WITH LOGIN PASSWORD {password}").format(
                        user=user, password=sql.Literal(passw)
                    )
                )
                c.execute(
                    sql.SQL("GRANT {user} TO {creator}").format(
                        user=user, creator=sql.Identifier(conn.info.user)
                    )
                )

    def create_ro_user(self, thing, user_prefix: str = ""):
        with self.db.connection() as conn:
            with conn.cursor() as c:
                ro_username = user_prefix.lower() + thing.database.ro_username.lower()
                ro_user = sql.Identifier(ro_username)
                schema = sql.Identifier(thing.database.schema.lower())
                ro_passw = decrypt(thing.database.ro_password, get_crypt_key())

                c.execute(
                    sql.SQL(
                        "CREATE ROLE {ro_user} WITH LOGIN PASSWORD {ro_password}"
                    ).format(ro_user=ro_user, ro_password=sql.Literal(ro_passw))
                )

                c.execute(
                    sql.SQL("GRANT {ro_user} TO {creator}").format(
                        ro_user=ro_user, creator=sql.Identifier(conn.info.user)
                    )
                )

                # Allow tcp connections to database with new user
                c.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {db_name} TO {ro_user}").format(
                        ro_user=ro_user, db_name=sql.Identifier(conn.info.dbname)
                    )
                )

                c.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA {schema} TO {ro_user}").format(
                        ro_user=ro_user, schema=schema
                    )
                )

    def password_has_changed(self, url, user, password):
        try:
            with psycopg.connect(url, user=user, password=password):
                pass
        except psycopg.OperationalError as e:
            if "password authentication failed" in str(e):
                return True
            raise e
        else:
            return False

    def maybe_update_password(self, user, password, db_url):
        # NOTE: currently unused function
        password = decrypt(password, get_crypt_key())
        if not self.password_has_changed(user, password, db_url):
            return

        logger.debug(f"update password for user {user}")
        with self.db.connection() as conn:
            with conn.cursor() as c:
                c.execute(
                    sql.SQL("ALTER USER {user} WITH PASSWORD {password}").format(
                        user=sql.Identifier(user), password=sql.Identifier(password)
                    )
                )

    def create_schema(self, thing):
        with self.db.connection() as conn:
            with conn.cursor() as c:
                schema = sql.Identifier(thing.database.schema.lower())
                user = sql.Identifier(thing.database.username.lower())
                c.execute(
                    sql.SQL(
                        "CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION {user}"
                    ).format(schema=schema, user=user)
                )

    def deploy_ddl(self, thing):
        file = os.path.join(os.path.dirname(__file__), "sql", "postgres-ddl.sql")
        with open(file) as fh:
            query = fh.read()

        with self.db.connection() as conn:
            with conn.cursor() as c:
                schema = sql.Identifier(thing.database.schema.lower())
                user = sql.Identifier(thing.database.username.lower())
                # Set search path for current session
                c.execute(sql.SQL("SET search_path TO {0}").format(schema))
                # Allow tcp connections to database with new user
                c.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {db_name} TO {user}").format(
                        user=user, db_name=sql.Identifier(conn.info.dbname)
                    )
                )
                # Set default schema when connecting as user
                c.execute(
                    sql.SQL(
                        "ALTER ROLE {user} SET search_path to {schema}, public"
                    ).format(user=user, schema=schema)
                )
                # Grant schema to new user
                c.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA {schema}, public TO {user}").format(
                        schema=schema, user=user
                    )
                )
                # Equip new user with all grants
                c.execute(
                    sql.SQL("GRANT ALL ON SCHEMA {schema} TO {user}").format(schema=schema, user=user)
                )
                # deploy the tables and indices and so on
                c.execute(query)

                c.execute(
                    sql.SQL(
                        "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {schema} TO {user}"
                    ).format(schema=schema, user=user)
                )

                c.execute(
                    sql.SQL(
                        "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {schema} TO {user}"
                    ).format(schema=schema, user=user)
                )

    def deploy_dml(self, thing):
        file = os.path.join(os.path.dirname(__file__), "sql", "postgres-dml.sql")
        with open(file) as fh:
            query = fh.read()
        with self.db.connection() as conn:
            with conn.cursor() as c:
                schema = sql.Identifier(thing.database.schema.lower())
                c.execute(sql.SQL("SET search_path TO {0}").format(schema))
                c.execute(query)

    def grant_sta_select(self, thing, user_prefix: str):
        schema = sql.Identifier(thing.database.schema.lower())
        sta_user = sql.Identifier(
            user_prefix.lower() + thing.database.ro_username.lower()
        )
        with self.db.connection() as conn:
            with conn.cursor() as c:
                # Set default schema when connecting as user
                c.execute(
                    sql.SQL(
                        "ALTER ROLE {sta_user} SET search_path to {schema}, public"
                    ).format(sta_user=sta_user, schema=schema)
                )

                # grant read rights to newly created views in schema to user
                c.execute(
                    sql.SQL(
                        "GRANT SELECT ON ALL TABLES in SCHEMA {schema} TO {sta_user}"
                    ).format(sta_user=sta_user, schema=schema)
                )

                c.execute(
                    sql.SQL(
                        "GRANT SELECT ON ALL SEQUENCES in SCHEMA {schema} TO {sta_user}"
                    ).format(sta_user=sta_user, schema=schema)
                )

                c.execute(
                    sql.SQL(
                        "GRANT EXECUTE ON ALL FUNCTIONS in SCHEMA {schema} TO {sta_user}"
                    ).format(sta_user=sta_user, schema=schema)
                )

    def grant_grafana_select(self, thing, user_prefix: str):
        with self.db.connection() as conn:
            with conn.cursor() as c:
                schema = sql.Identifier(thing.database.schema.lower())
                grf_user = sql.Identifier(
                    user_prefix.lower() + thing.database.ro_username.lower()
                )

                # Set default schema when connecting as user
                c.execute(
                    sql.SQL("ALTER ROLE {grf_user} SET search_path to {schema}").format(
                        grf_user=grf_user, schema=schema
                    )
                )

                c.execute(sql.SQL("SET search_path TO {schema}").format(schema=schema))

                c.execute(
                    sql.SQL(
                        "REVOKE ALL ON ALL TABLES IN SCHEMA {schema}, public FROM {grf_user}"
                    ).format(grf_user=grf_user, schema=schema)
                )

                c.execute(
                    sql.SQL(
                        "GRANT SELECT ON TABLE thing, datastream, observation, "
                        'journal, datastream_properties, "LOCATIONS", "THINGS", '
                        '"THINGS_LOCATIONS", "SENSORS", "OBS_PROPERTIES", "DATASTREAMS", '
                        '"OBSERVATIONS" TO {grf_user}'
                    ).format(grf_user=grf_user, schema=schema)
                )

    def create_frost_views(self, thing):
        base_path = os.path.join(os.path.dirname(__file__), "sql", "sta_views")
        files = [
            os.path.join(base_path, "schema_context.sql"),
            os.path.join(base_path, "thing.sql"),
            os.path.join(base_path, "location.sql"),
            os.path.join(base_path, "thing_location.sql"),
            os.path.join(base_path, "historical_location.sql"),
            os.path.join(base_path, "sensor.sql"),
            os.path.join(base_path, "observed_property.sql"),
            os.path.join(base_path, "datastream.sql"),
            os.path.join(base_path, "observation.sql"),
            os.path.join(base_path, "feature.sql"),
            os.path.join(base_path, "helper_views", "ts_coordinates_dyn_x_y_z.sql"),
            os.path.join(base_path, "helper_views", "foi_ts_action_type.sql"),
            os.path.join(base_path, "helper_views", "foi_ts_coordinates.sql"),
            os.path.join(base_path, "helper_views", "obs_ts_action_type.sql"),
            os.path.join(base_path, "helper_views", "obs_ts_coordinates.sql"),
            os.path.join(base_path, "new_observation.sql"),
            os.path.join(base_path, "new_feature.sql"),
        ]

        schema = thing.database.schema.lower()
        user = sql.Identifier(thing.database.username.lower())
        SMS_URL = os.environ.get("SMS_URL")
        CV_URL = os.environ.get("CV_URL")

        def escape_quote(s: str) -> str:
            return s.replace("'", "''")

        with self.db.connection() as conn:
            with conn.cursor() as c:
                schema_id = sql.Identifier(thing.database.schema.lower())
                c.execute(sql.SQL("SET search_path TO {schema}, public").format(schema=schema_id))
                for file in files:
                    logger.debug(f"deploy file: {file}")
                    with open(file) as fh:
                        view = fh.read()
                    # This is a possible entry point for SQL injections. Ensure that we have
                    # full control over the values, especially that the value does not come
                    # from userinput. Additionally, we escape single quotes, prevent closing
                    # the outer quotes in the file.
                    view = view.replace("{tsm_schema}", f"{escape_quote(schema)}")
                    view = view.replace("{sms_url}", f"{escape_quote(SMS_URL)}")
                    view = view.replace("{cv_url}", f"{escape_quote(CV_URL)}")
                    c.execute(view)

    def create_grafana_views(self, thing):
        file = os.path.join(
            os.path.dirname(__file__),
            "sql",
            "grafana_views",
            "datastream_properties.sql",
        )
        with open(file) as fh:
            view = fh.read()
        with self.db.connection() as conn:
            with conn.cursor() as c:
                schema = sql.Identifier(thing.database.schema.lower())
                c.execute(sql.SQL("SET search_path TO {0}").format(schema))
                c.execute(view)

    def upsert_thing(self, thing) -> bool:
        """Returns True for insert and False for update"""
        schema_name = thing.database.schema.lower()
        query = (
            f"INSERT INTO {schema_name}.thing (name, uuid, description, properties) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (uuid) DO UPDATE SET "
            "name = EXCLUDED.name, "
            "description = EXCLUDED.description, "
            "properties = EXCLUDED.properties "
            "RETURNING (xmax = 0)"
        )
        params = (
            thing.name,
            thing.uuid,
            thing.description,
            json.dumps(thing.properties or {}),
        )
        with self.db.connection() as conn:
            with conn.cursor() as c:
                c.execute(query, params)
                result = c.fetchone()
        return result

    def thing_exists(self, username: str):
        with self.db.connection() as conn:
            with conn.cursor() as c:
                c.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", [username])
                return len(c.fetchall()) > 0

    def user_exists(self, username: str):
        with self.db.connection() as conn:
            with conn.cursor() as c:
                c.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", [username])
                return len(c.fetchall()) > 0

    def schema_exists(self, schema: str):
        with self.db.connection() as conn:
            with conn.cursor() as c:
                c.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name=%s", [schema])
                return len(c.fetchall()) > 0


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInPostgresHandler().run_loop()
