import psycopg
from timeio.databases import Database
from timeio.common import get_envvar
import json
import timeio.mqtt as mqtt

import logging

logger = logging.getLogger("publish_all_things")


class PublishAllThings:
    def __init__(self):
        self.db = Database(get_envvar("DATABASE_DSN"))
        self.things_uuids = []
        self.publish_topic = get_envvar("MQTT_PUBLISH_TOPIC")

    def fetch_things(self):
        with self.db.connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        Select uuid::TEXT from config_db.thing;
                        """)
                    logger.info(f"Fetching uuids of all stored things")
                    self.things_uuids = [row[0] for row in cursor.fetchall()]

                    return self
            except psycopg.Error as e:
                logger.error(f"Error occurred during fetching things: {e}")
                if conn:
                    conn.rollback()

    def publish_all_things(self):
        for thing_uuid in self.things_uuids:
            print(f"Publishing thing: {thing_uuid}")
            logger.info(
                f"Publishing thing uuid: {thing_uuid} to topic: {self.publish_topic}"
            )
            # TODO: use a regular mqtt client. publish_single is for
            #  one-time use only.
            mqtt.publish_single(
                self.publish_topic, json.dumps({"thing_uuid": thing_uuid})
            )


if __name__ == "__main__":
    PublishAllThings().fetch_things().publish_all_things()
