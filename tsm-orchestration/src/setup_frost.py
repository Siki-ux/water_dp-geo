import logging

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.typehints import MqttPayload
from timeio import frost

logger = logging.getLogger("frost-setup")


class CreateFrostInstanceHandler(AbstractHandler):

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
        self.tomcat_proxy_url = get_envvar("TOMCAT_PROXY_URL")
        self.configdb_dsn = get_envvar("CONFIGDB_DSN")

    def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.configdb_dsn)
        frost.write_context_file(
            schema=thing.database.schema,
            user=f"sta_{thing.database.ro_username.lower()}",
            password=thing.database.ro_password,
            db_url=thing.database.ro_url,
            tomcat_proxy_url=self.tomcat_proxy_url,
        )


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateFrostInstanceHandler().run_loop()
