from __future__ import annotations

import json
import logging
import sys
import os
import threading
import time
import traceback
import typing
from abc import ABC, abstractmethod

import paho.mqtt.publish
import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage

from timeio.errors import (
    UserInputError,
    DataNotFoundError,
    ParsingError,
    NoDataWarning,
    ProcessingError,
)

logger = logging.getLogger("mqtt-handler")


class AbstractHandler(ABC):
    def __init__(
        self,
        topic: str,
        mqtt_broker: str,
        mqtt_user: str,
        mqtt_password: str,
        mqtt_client_id: str,
        mqtt_qos: int,
        mqtt_clean_session: bool,
    ):
        self.topic = topic
        self.mqtt_broker = mqtt_broker
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        self.mqtt_client_id = mqtt_client_id
        self.mqtt_qos = mqtt_qos
        self.mqtt_clean_session = mqtt_clean_session
        self.mqtt_host = mqtt_broker.split(":")[0]
        self.mqtt_port = int(mqtt_broker.split(":")[1])
        self.mqtt_client = mqtt.Client(
            client_id=mqtt_client_id,
            clean_session=self.mqtt_clean_session,
        )
        self.mqtt_client.suppress_exceptions = False
        self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_subscribe = self.on_subscribe
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_log = self.on_log
        # healthcheck settings
        self._last_message = time.time()
        self._healthcheck_topic = f"health/{self.mqtt_client_id}/ping"
        self._healthcheck_status_topic = f"health/{self.mqtt_client_id}/status"
        self._healthcheck_interval = int(
            os.getenv("MQTT_HEALTHCHECK_INTERVAL", 60)
        )  # seconds
        self._healthcheck_timeout = int(
            os.getenv("MQTT_HEALTHCHECK_TIMEOUT", 600)
        )  # seconds
        self._st = threading.Thread(target=self._healthcheck_sender, daemon=True)
        self._wt = threading.Thread(target=self._healthcheck_watcher, daemon=True)
        self._mid_to_topic = {}

    def run_loop(self) -> typing.NoReturn:
        logger.info("Setup ok, starting listening loop, healtcheck sender and watcher")
        self._st.start()
        self._wt.start()
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        self.mqtt_client.loop_forever()

    def on_log(self, client: mqtt.Client, userdata, level, buf):
        logger.debug(f"%s: %s", level, buf)

    def on_connect(self, client: mqtt.Client, userdata, flags, rc):
        if rc == 0:
            logger.info(
                f"Connected to %r with client ID: %s",
                self.mqtt_broker,
                self.mqtt_client._client_id.decode(),
            )
            # Subscribe to topic in on_connect callback
            # to make sure we re-subscribe after a reconnect
            res, mid = self.mqtt_client.subscribe(self.topic, self.mqtt_qos)
            self._mid_to_topic[mid] = self.topic
            res, mid = self.mqtt_client.subscribe(self._healthcheck_topic, 0)
            self._mid_to_topic[mid] = self._healthcheck_topic
            return
        logger.error(f"Failed to connect to %r, return code: %s", self.mqtt_broker, rc)

    def on_subscribe(self, client: mqtt.Client, userdata, mid, granted_qos):
        topic = self._mid_to_topic.get(mid, "(unknown)")
        logger.info(f"Subscribed to topic {topic} with QoS {granted_qos[0]}")

    def on_message(self, client: mqtt.Client, userdata, message: MQTTMessage):
        self._last_message = time.time()
        if message.topic == self._healthcheck_topic:
            logger.debug(f"Ping received.")
            return

        logger.info(
            "\n\n======================= NEW MESSAGE ========================\n"
            f"Topic: %r, QoS: %s, Timestamp: %s",
            message.topic,
            message.qos,
            message.timestamp,
        )

        try:
            content = self._decode(message)
        except Exception:
            logger.critical(
                f"\n====================== CRITICAL ERROR ======================\n"
                f"Status: PARSING ERROR  (Decoding/parsing of payload failed)\n"
                f"Payload:\n{message.payload!r}\n"
                f"{traceback.format_exc()}"
                f"========================= SYS EXIT =========================\n",
            )
            # We exit now, because otherwise the client.on_log would print
            # the exception again (with unnecessary clutter)
            sys.exit(1)

        try:
            logger.debug(f"calling %s.act()", self.__class__.__qualname__)
            self.act(content, message)

        except (UserInputError, ParsingError):
            logger.error(
                f"\n======================== USER ERROR ========================\n"
                f"Status: ERROR  (An error because of user data or input)\n"
                f"Content:\n{content!r}\n"
                f"{traceback.format_exc()}"
                f"======================== USER ERROR ========================\n",
            )
            return
        except (DataNotFoundError, NoDataWarning):
            logger.error(
                f"\n======================== DATA ERROR ========================\n"
                f"Status: ERROR  (Data is missing)\n"
                f"Content:\n{content!r}\n"
                f"{traceback.format_exc()}"
                f"======================== DATA ERROR ========================\n",
            )
            return

        except ProcessingError:
            logger.error(
                f"\n=================== PROCESSING ERROR ========================\n"
                f"Status: ERROR  (Processing failed)\n"
                f"Content:\n{content!r}\n"
                f"{traceback.format_exc()}"
                f"===================== PROCESSING ERROR ========================\n",
            )
            return

        except Exception:
            logger.critical(
                f"\n====================== CRITICAL ERROR ======================\n"
                f"Status: UNHANDLED ERROR  (See exception and traceback below)\n"
                f"Content:\n{content!r}\n"
                f"{traceback.format_exc()}"
                f"========================= SYS EXIT =========================\n",
            )
            # We exit now, because otherwise the client.on_log would print
            # the exception again (with unnecessary clutter)
            sys.exit(1)

        logger.info(
            f"\n===================== PROCESSING DONE ======================\n"
            f"Status: Success  (Message was processed successfully)\n"
            f"===================== PROCESSING DONE ======================\n",
        )

    def _healthcheck_sender(self):
        while True:
            payload = json.dumps({"ping": time.asctime()})
            self.mqtt_client.publish(
                self._healthcheck_topic, payload=payload, qos=0, retain=False
            )
            time.sleep(self._healthcheck_interval)

    def _healthcheck_watcher(self):
        while True:
            if time.time() - self._last_message > self._healthcheck_timeout:
                msg = f"MQTT-Loop stuck! Last message received at {time.asctime(time.localtime(self._last_message))}"
                logger.error(msg)
                self.mqtt_client.publish(
                    self._healthcheck_status_topic, payload=msg, qos=0, retain=False
                )
            time.sleep(self._healthcheck_interval)

    def _decode(self, message: MQTTMessage) -> typing.Any:
        """
        This decodes the message from utf-8 and also try to decode json to python
        objects. If the object is not json (e.g. plain strings or a datetime object
        like 2022-22-22T11:11:11) the object itself is returned instead.

        Parameters
        ----------
        message : MQTTMessage
            Message to decode.

        Returns
        -------
        content:
            The decoded content

        Raises
        ------
        UnicodeDecodeError
            If the raw message is not 'utf-8' encoded.
        """
        # Hint: json.loads also decodes single numeric values,
        # the constants `null`, +/-`Infinity` and `NaN`.
        decoded: str = message.payload.decode("utf-8")
        try:
            decoded = json.loads(decoded)
        except json.JSONDecodeError:
            logger.warning(
                f"Message content is not valid json. (That's ok, but unusual)"
            )
        return decoded

    @abstractmethod
    def act(self, content: typing.Any, message: MQTTMessage):
        """
        Subclasses must overwrite this function.

        The calling function will handle the following exceptions:
         - timeio.errors.ParsingError
         - timeio.errors.UserInputError
         - timeio.errors.DataNotFoundError
         - timeio.errors.NoDataWarning

         Other exceptions will lead to a system exit.
        """

        raise NotImplementedError


def _get_settings_from_env():
    try:
        _broker = os.environ["MQTT_BROKER"]
        return {
            "qos": int(os.environ["MQTT_QOS"]),
            "hostname": _broker.split(":")[0],
            "port": int(_broker.split(":")[1]),
            "auth": {
                "username": os.environ["MQTT_USER"],
                "password": os.environ["MQTT_PASSWORD"],
            },
        }
    except KeyError as e:
        raise EnvironmentError(f"Missing environment variable {e}")


def publish_single(topic, payload: str, client_id: str = ""):
    """
    Publish a single mqtt message to a broker, then disconnect cleanly.
    DO NOT CALL THIS RAPIDLY REPEATEDLY, use a normal paho.mqtt.client
    instead.
    """
    paho.mqtt.publish.single(
        **_get_settings_from_env(), topic=topic, payload=payload, client_id=client_id
    )
