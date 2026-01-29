from __future__ import annotations

import logging

from minio import Minio
from minio.notificationconfig import NotificationConfig, QueueConfig
from minio.error import S3Error
from minio.datatypes import Bucket
from minio.commonconfig import GOVERNANCE, Tags
from minio.objectlockconfig import ObjectLockConfig, YEARS

logger = logging.getLogger("minio-cli-wrapper")


class MinioClient:

    def __init__(
        self,
        url: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        secure=False,
    ):

        self.url = url
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure

        # Python SDK minio client
        self.minio = Minio(
            self.url,
            secure=self.secure,
            access_key=self.access_key,
            secret_key=self.secret_key,
        )

    def bucket_exists(self, bucket_name: str) -> bool:
        return self.minio.bucket_exists(bucket_name)

    def get_bucket(self, bucket_name: str) -> Bucket | None:
        # Unfortunately, the MinIO Python SDK does not provide a get_bucket method
        if not self.bucket_exists(bucket_name):
            return None
        buckets = self.minio.list_buckets()
        for b in buckets:
            if b.name == bucket_name:
                return b

    def make_bucket(self, bucket_name: str, object_lock: bool = True) -> Bucket:
        # Unfortunately, the MinIO Python SDK does not return a Bucket object
        self.minio.make_bucket(bucket_name, object_lock=object_lock)
        return self.get_bucket(bucket_name)

    def get_bucket_retention(self, bucket_name: str) -> ObjectLockConfig | None:
        try:
            return self.minio.get_object_lock_config(bucket_name)
        except S3Error as e:
            if e.code == "ObjectLockConfigurationNotFoundError":
                return None
            raise

    def set_bucket_retention(
        self, bucket_name: str, years: int = 100
    ) -> ObjectLockConfig:
        lock_config = ObjectLockConfig(GOVERNANCE, years, YEARS)
        self.minio.set_object_lock_config(bucket_name, lock_config)
        return self.get_bucket_retention(bucket_name=bucket_name)

    def set_bucket_notification(
        self, bucket_name: str, events: list[str] | None = None
    ) -> NotificationConfig:
        events = events or [
            "s3:ObjectCreated:CompleteMultipartUpload",
            "s3:ObjectCreated:Copy",  # <- not sure whether we want this one...
            "s3:ObjectCreated:Post",
            "s3:ObjectCreated:Put",
        ]
        config = NotificationConfig(
            queue_config_list=[
                QueueConfig(
                    queue="arn:minio:sqs::LOCAL_BROKER:mqtt",
                    events=events,
                    config_id="1",
                ),
            ],
        )
        self.minio.set_bucket_notification(bucket_name=bucket_name, config=config)
        return self.minio.get_bucket_notification(bucket_name=bucket_name)

    def set_bucket_tags(self, bucket_name: str, tags: Tags | None = None) -> Tags:
        self.minio.set_bucket_tags(bucket_name, tags)
        return self.minio.get_bucket_tags(bucket_name)
