#!/usr/bin/env python
from __future__ import annotations

import json
import logging
import sys
from typing import Any

import paho.mqtt.client as mqtt
from psycopg_pool import ConnectionPool
from timeio.typehints import MqttPayload, v1
from timeio.common import get_envvar
from timeio.configdb import (
    store_qaqc_config,
    store_thing_config,
    store_project_config,
)
from timeio.version import __version__ as timeio_version

logger = logging.getLogger("configdb-updater")
__version__ = "0.2.0"


def prepare_data_by_version(data: dict[str, Any]) -> dict[str, Any]:
    """
    Modify the mqtt content by version to get a uniform structure.
    Note that keys have no fix order !

    Returns :
    {
     version: <int>,
     uuid: <str/uuid>
     name: <str>
     description: <str>
     ingest_type: <str>
     project: {...}
     database: {...}
     # ==== OPTIONAL DATA (keys are mandatory) ====
     parsers: {default: <int> | None, parsers: [{...},...]} | None
     raw_data_storage: {...} | None
     mqtt_device_type: <str> | None
     mqtt: {...} | None
     external_sftp: {...} | None
     external_api: {...} | None
     qaqc: {...} | None     (legacy (thing-)qaqc! not used in versions > 6)
    }

    """
    if data["version"] == 4:
        # tsm-frontend/GL71
        if d := data.get("external_sftp"):
            d["private_key"] = "no-key-in-message-version-4"  # always None
        # tsm-frontend/GL70
        if (mqtt := data.pop("mqtt_authentication_credentials", None)) is None:
            raise KeyError(
                "malformed message content, missing top level "
                "key: 'mqtt_authentication_credentials'"
            )
        # rename mqtt_authentication_credentials -> mqtt
        data["mqtt"] = mqtt
        if d := data.get("mqtt"):
            d.pop("properties", None)  # unused
            d.setdefault("password", "no-password-in-message-version-4")  # missing
            d.setdefault("topic", d.get("description"))  # missing
        if d := data.get("database"):
            d.setdefault("schema", d.get("username"))  # missing
        if d := data.get("parsers", {}).get("parsers"):
            for parser in d:
                parser.setdefault("name", "no-parser-name")  # missing

    elif data["version"] == 5:
        if d := data.get("mqtt"):
            d.pop("uri", None)  # unused

    elif data["version"] == 6:
        if d := data.get("mqtt"):
            d.pop("uri", None)  # unused

    elif data["version"] == 7:
        if d := data.get("mqtt"):
            d.pop("uri", None)  # unused

    else:
        raise NotImplementedError(
            f"Content version {data['version']} is not implemented yet."
        )

    # general stuff
    # =============

    # set raw_data_storage (S3) to None if keys have no relevant values
    if data.get("raw_data_storage", {}).get("bucket_name", None) is None:
        data["raw_data_storage"] = None

    # set parsers to None if keys have no relevant values
    if data.get("parsers", {}).get("default", None) is None:
        data["parsers"] = None

    # set mqtt to None if keys have no relevant values
    if data.get("mqtt", {}).get("username", None) is None:
        data["mqtt"] = None
    else:
        # move top level mqtt_device_type to mqtt key
        data["mqtt"]["mqtt_device_type"] = data["mqtt_device_type"]

    # set ext_sftp to None if keys have no relevant values
    if data.get("external_sftp", {}).get("uri", None) is None:
        data["external_sftp"] = None

    # set ext_sftp to None if keys have no relevant values
    if data.get("external_api", {}).get("type", None) is None:
        data["external_api"] = None

    # only relevant for versions <= 6
    data.setdefault("qaqc", None)

    return data


def qaqc_update(client: mqtt.Client, userdata: dict, msg: mqtt.MQTTMessage):
    logger.info(f"==================== new {msg.topic} message ====================")
    db: ConnectionPool = userdata["db"]
    pub_topic: str = userdata["publish_topic"]
    pub_qos: int = userdata["publish_qos"]

    section = "Parsing message content"
    data = None
    try:
        data: MqttPayload.QaqcConfigV3_T = json.loads(msg.payload.decode())
        if (name := data.get("name")) is None:
            raise ValueError("mandatory field 'name' is not present in data")
        if (version := data.get("version")) is None:
            raise ValueError("mandatory field 'version' is not present in data")
        logger.debug(f"Message content version: {version}")

        logger.info(f"Processing QC config {name!r}. Project: {data['project_uuid']}")
        section = "Processing QC settings"
        with db.connection() as conn:
            store_qaqc_config(conn, data, legacy=False)
        # this publish caused an error: https://ufz-rdm.atlassian.net/jira/software/c/projects/TSM/boards/105?selectedIssue=TSM-563
        # no service currently needs this message so we comment out the publish
        # section = "sending mqtt message"
        # logger.debug(f"Inform downstream services about update of QC.")
        # payload = json.dumps({"qaqc": data["name"]})
        # client.publish(topic=pub_topic, payload=payload, qos=pub_qos)
    except Exception:
        if data is not None:
            detail = f"Message content: {data}"
        else:
            detail = f"msg.payload: {msg.payload!r}"
        logger.exception(f"{section} failed. {detail}\n")
    else:
        logger.info(f"Successfully updated QC settings")


def thing_update(client: mqtt.Client, userdata: dict, msg: mqtt.MQTTMessage):
    logger.info(f"==================== new {msg.topic} message ====================")
    db: ConnectionPool = userdata["db"]
    pub_topic: str = userdata["publish_topic"]
    pub_qos: int = userdata["publish_qos"]

    section = "Parsing message content"
    try:
        data: dict = json.loads(msg.payload.decode())
        if (thing_uuid := data.get("uuid")) is None:
            raise ValueError("mandatory field 'uuid' is not present in data")
        if (version := data.get("version")) is None:
            raise ValueError("mandatory field 'version' is not present in data")
        logger.debug(f"Message content version: {version}")
        data = prepare_data_by_version(data)
        logging.info(f"thing: {thing_uuid} ({data.get('name', 'UNNAMED')})")

        # We only commit changes if all inserts were successful,
        # and we also successfully informed downstream services
        # via mqtt, if anything goes wrong we roll back. This is
        # done automatically by the connection context manager.
        with db.connection() as conn:

            proj_id = store_project_config(conn, data)

            qid = None
            if version <= 6:
                # Currently we have two different qc workflows.
                # The legacy workflow, by which the QC Settings are stored with the
                # thing itself and the new qc workflow which has its own input mask
                # in the frontend and is bound to a project.
                # The former is handled here by extracting the relevant keys from the
                # mqtt message and with them calling `store_qaqc_config`.
                # The latter is triggererd by another mqtt message and processed in its
                # own mqtt handler `qaqc_update` above.
                section = "Processing legacy QC"
                proj_uuid = data["project"]["uuid"]
                idx = data["qaqc"]["default"]
                cnf = data["qaqc"]["configs"][idx]
                cnf["version"] = v1
                cnf["project_uuid"] = proj_uuid
                cnf: MqttPayload.QaqcConfigV1_T
                logger.info(f"Processing legacy QC settings from thing {thing_uuid}")
                qid = store_qaqc_config(conn, cnf, legacy=True)

            section = "Processing thing"
            logger.info(f"processing data for thing {thing_uuid}")
            store_thing_config(conn, data, qid, proj_id)

            section = "Sending mqtt message"
            logger.debug(f"inform downstream services about update of thing")
            payload = json.dumps({"thing": thing_uuid})
            client.publish(topic=pub_topic, payload=payload, qos=pub_qos)
    except Exception:
        logger.exception(f"{section} failed.\n")
    else:
        logger.info(f"Successfully updated thing {thing_uuid}")


def on_connect(client, userdata, flags, rc, properties=None):
    logger.info("Connected to MQTT Broker, rc=%s", rc)
    client.subscribe("frontend_thing_update", qos=subscribe_qos)
    client.subscribe("qaqc_settings_update", qos=subscribe_qos)
    logger.info("Subscribed to frontend_thing_update, qaqc_settings_update")
    logger.info(f"Waiting for messages ...")


def on_disconnect(client, userdata, flags, rc, properties=None):
    if rc != 0:
        logger.warning("Unexpected disconnect from MQTT Broker. rc=%s", rc)
    else:
        logger.info("Disconnected from MQTT Broker.")


def on_log(client, userdata, level, buf):
    logger.debug(f"MQTT Log: {buf}")


if __name__ == "__main__":
    if len(sys.argv) != 1:
        if sys.argv[1] in ["-v", "--version"]:
            print(sys.argv[0], __version__)
            print("timeio", timeio_version)
            sys.exit(0)
        raise ValueError(
            "The script takes no arguments except -v/--version, "
            "which prints the version and exits."
        )

    log_level = get_envvar("LOG_LEVEL", "INFO")
    logging.basicConfig(level=log_level)

    broker_host = get_envvar("MQTT_BROKER_HOST")
    broker_port = get_envvar("MQTT_BROKER_PORT", cast_to=int)
    user = get_envvar("MQTT_USER")
    password = get_envvar("MQTT_PASSWORD")
    subscribe_qos = get_envvar("MQTT_SUBSCRIBE_QOS", cast_to=int)
    client_id = get_envvar("MQTT_CLIENT_ID", None)
    clean_session = get_envvar("MQTT_CLEAN_SESSION", False, cast_to=bool)
    publish_topic = get_envvar("MQTT_PUBLISH_TOPIC")
    publish_qos = get_envvar("MQTT_PUBLISH_QOS", cast_to=int)

    dsn = get_envvar("CONFIGDB_DSN")
    # we only have one active thread that process a message at a time,
    # so we just need a single DB connection. Due to reconnect problems
    # with in the past we use a ConnectionPool with a single connection,
    # that checks the quality of connection (pings the DB) each time
    # the connection is served to a new client.
    db_conn_pool = ConnectionPool(
        dsn,
        min_size=1,
        max_size=2,
        open=True,
        check=ConnectionPool.check_connection,
    )
    timeout = get_envvar("CONFIGDB_CONNECTION_INITIAL_TIMEOUT", None, cast_to=int)
    db_conn_pool.wait(timeout=timeout)
    logger.info("connected to configdb")

    mqtt_client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,  # noqa
        client_id=client_id,  # noqa
        clean_session=clean_session,
    )
    mqtt_client.username_pw_set(user, password)
    mqtt_client.user_data_set(
        {
            "publish_topic": publish_topic,
            "publish_qos": publish_qos,
            "db": db_conn_pool,
        }
    )
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_log = on_log
    # Assign message handlers
    mqtt_client.message_callback_add("frontend_thing_update", thing_update)
    mqtt_client.message_callback_add("qaqc_settings_update", qaqc_update)

    try:
        # Connect to MQTT broker and subscribe to topics (via on_connect callback)
        mqtt_client.connect(broker_host, int(broker_port))
        mqtt_client.loop_forever()
    finally:
        db_conn_pool.close()
