from __future__ import annotations

import logging

from timeio.minio.client import MinioClient
from timeio.minio.admin_client import MinioAdminClient

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.crypto import decrypt, get_crypt_key
from timeio.typehints import MqttPayload

logger = logging.getLogger("minio-setup")


class CreateThingInMinioHandler(AbstractHandler):
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
        # Custom minio client
        self.minio = MinioClient(
            url=get_envvar("MINIO_URL"),
            access_key=get_envvar("MINIO_ACCESS_KEY"),
            secret_key=get_envvar("MINIO_SECURE_KEY"),
            secure=get_envvar("MINIO_SECURE", default=True, cast_to=bool),
        )
        # Custom minio admin client
        self.minio_admin = MinioAdminClient(
            url=get_envvar("MINIO_URL"),
            access_key=get_envvar("MINIO_ACCESS_KEY"),
            secret_key=get_envvar("MINIO_SECURE_KEY"),
            secure=get_envvar("MINIO_SECURE", default=True, cast_to=bool),
        )
        self.configdb_dsn = get_envvar("CONFIGDB_DSN")

    def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.configdb_dsn)
        if thing.raw_data_storage is None:
            logger.info(
                f"Ignoring message, because no s3 storage is associated "
                f"with the thing {thing.uuid} ({thing.name})"
            )
            return
        user = thing.raw_data_storage.username
        passw = decrypt(thing.raw_data_storage.password, get_crypt_key())
        bucket = thing.raw_data_storage.bucket_name

        logger.debug(f"Adding MinIO user {user}")
        self.minio_admin.user_add(access_key=user, secret_key=passw)

        logger.debug(f"Creating MinIO policy {user} for bucket {bucket}")
        policy = self.minio_admin.build_bucket_policy(bucket_name=bucket)
        self.minio_admin.policy_add(
            policy_name=user,
            policy=policy,
        )

        logger.debug(f"Assigning policy {user} to user {user}")
        self.minio_admin.user_policy_set(policy_name=user, user=user)

        if self.minio.bucket_exists(bucket_name=bucket):
            logger.debug(f"Bucket {bucket} already exists")
        else:
            logger.debug(f"Creating bucket {bucket}")
            self.minio.make_bucket(bucket_name=bucket, object_lock=True)

        if self.minio.get_bucket_retention(bucket_name=bucket):
            logger.debug(f"Bucket {bucket} already has retention set")
        else:
            logger.debug(f"Setting retention for bucket {bucket}")
            self.minio.set_bucket_retention(bucket_name=bucket, years=100)

        logger.debug(f"Setting notification for bucket {bucket}")
        self.minio.set_bucket_notification(bucket_name=bucket)

        # we could set bucket quotas here...


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInMinioHandler().run_loop()
