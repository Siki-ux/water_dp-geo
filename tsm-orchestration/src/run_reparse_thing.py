#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
from fnmatch import fnmatch

import click
from datetime import datetime, timezone
from minio import Minio
import paho.mqtt.client as mqtt

from timeio.feta import Thing
from timeio.journaling import Journal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reprocess-files")
journal = Journal("Reprocessing")


def setupMQTT(host, username, password):
    host, port = host.split(":")
    port = int(port)

    client = mqtt.Client(client_id="reparse-files", clean_session=False)
    client.enable_logger(logger)

    client.username_pw_set(username, password)

    if port == 8883:
        client.tls_set()
        # client.tls_insecure_set(True)

    client.suppress_exceptions = False
    client.connect(host, port, keepalive=60)

    return client


@click.command()
@click.option(
    "--configdb-dsn",
    default="postgresql://configdb:configdb@localhost:5432/postgres",
    envvar="CONFIGDB_DSN",
)
@click.option(
    "--thing-uuid", default="0a308373-ab29-4317-b351-1443e8a1babd", envvar="THING_UUID"
)
@click.option("--minio-host", default="localhost:9000", envvar="MINIO_HOST")
@click.option("--minio-user", default="minioadmin", envvar="MINIO_USER")
@click.option("--minio-password", default="minioadmin", envvar="MINIO_PASSWORD")
@click.option("--mqtt-host", default="localhost:1883", envvar="MQTT_HOST")
@click.option("--mqtt-user", default="mqtt", envvar="MQTT_USER")
@click.option("--mqtt-password", default="mqtt", envvar="MQTT_PASSWORD")
@click.option("--filename-pattern", default=None)
@click.option("--start-date", default=None)
@click.option("--end-date", default=None)
def main(
    configdb_dsn,
    thing_uuid,
    minio_host,
    minio_user,
    minio_password,
    mqtt_host,
    mqtt_user,
    mqtt_password,
    filename_pattern,
    start_date,
    end_date,
):
    store = Thing.from_uuid(thing_uuid, dsn=configdb_dsn).raw_data_storage

    minio = Minio(
        endpoint=minio_host,
        access_key=minio_user,
        secret_key=minio_password,
        secure=not minio_host.startswith("localhost"),
    )
    mqtt = setupMQTT(mqtt_host, mqtt_user, mqtt_password)

    bucket = store.bucket
    fnpattern_from_thing = store.filename_pattern
    fnpattern_from_job = filename_pattern
    if start_date:
        start = datetime.fromisoformat(start_date)
        start = start if start.tzinfo else start.replace(tzinfo=timezone.utc)
    if end_date:
        end = datetime.fromisoformat(end_date)
        end = end if end.tzinfo else end.replace(tzinfo=timezone.utc)

    mqtt.loop_start()

    message = {"EventName": "s3:ObjectCreated:Put", "reparsing": True}
    for obj in minio.list_objects(bucket):
        fname = obj.object_name
        fdate = obj.last_modified
        if fnmatch(fname, fnpattern_from_thing):
            cond2 = not fnpattern_from_job or fnmatch(fname, fnpattern_from_job)
            cond3 = True if not start_date else fdate >= start
            cond4 = True if not end_date else fdate <= end
            if cond2 and cond3 and cond4:
                message["Key"] = f"{bucket}/{fname}"
                logging.info(f"republishing file: {message['Key']}")
                result = mqtt.publish(
                    topic="object_storage_notification",
                    payload=json.dumps(message),
                    qos=1,
                )
                if result[0] != 0:
                    logger.warning(
                        f"Failed to deliver reprocessing message for file: {message['Key']}"
                    )

    mqtt.loop_stop()
    mqtt.disconnect()


if __name__ == "__main__":
    main()
