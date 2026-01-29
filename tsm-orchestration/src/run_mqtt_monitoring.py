from __future__ import annotations

import logging
import typing
import time
import psycopg

from datetime import datetime
from psycopg import sql

import paho.mqtt.client as mqtt


from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.common import get_envvar, setup_logging

logger = logging.getLogger("run-mqtt-monitoring")


class MqttMonitoringHandler(AbstractHandler):

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

        self.sub_topic = "$SYS/broker/"
        self.monitoring_schema = get_envvar("MONITORING_SCHEMA")
        self.dsn = get_envvar("DSN")

    def act(self, content: typing.Any, message: MQTTMessage):
        try:
            raw_message = self.fetch_data()
            parsed_message = self.parse_message(raw_message)
            self.write_into_db(parsed_message)
            logger.info("Successfully wrote mqtt broker metrics into TimeIO DB")
        except Exception as e:
            logger.error(
                f"Failed to receive and/or write mqtt broker metrics into TimeIO DB: {e}"
            )

    def fetch_data(self):
        message = {}

        def on_message(client, userdata, msg):
            if msg.topic == f"{self.sub_topic}version":
                return
            message["time"] = datetime.now()
            message[msg.topic] = msg.payload.decode()

        mqtt_client = mqtt.Client(
            client_id=f"{self.mqtt_client_id}_fetcher", clean_session=True
        )
        mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)
        mqtt_client.on_message = on_message
        mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        mqtt_client.subscribe(f"{self.sub_topic}#")
        mqtt_client.loop_start()
        time.sleep(2)
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

        return message

    def parse_message(self, raw_message):
        parsed_message = {}
        for k, v in raw_message.items():
            if k == "time":
                parsed_message["time"] = v
                continue
            clean_key = k[len(self.sub_topic) :] if k.startswith(self.sub_topic) else k
            clean_key = clean_key.replace("/", "_")
            clean_key = clean_key.replace(" ", "_")
            if clean_key == "uptime":
                parsed_message[clean_key] = v
            else:
                try:
                    parsed_message[clean_key] = float(v)
                except ValueError:
                    parsed_message[clean_key] = v

        return parsed_message

    def write_into_db(self, parsed_message):
        columns = list(parsed_message.keys())
        table_name = "mqtt_broker"

        query = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
            sql.Identifier(self.monitoring_schema),
            sql.Identifier(table_name),
            sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.SQL(", ").join(sql.Placeholder(k) for k in columns),
        )

        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, parsed_message)


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    MqttMonitoringHandler().run_loop()
