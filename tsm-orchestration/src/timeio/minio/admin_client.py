from __future__ import annotations

import json
import logging

from minio import MinioAdmin
from minio.credentials import StaticProvider

from .typehints import BucketQuotaT, UserT, PolicyT, PolicyEntitiesT, ServiceAccountT

logger = logging.getLogger("minio-cli-wrapper")


class MinioAdminClient:

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

        self.minio_admin = MinioAdmin(
            endpoint=url,
            secure=secure,
            credentials=StaticProvider(
                access_key=access_key,
                secret_key=secret_key,
            ),
        )

    @staticmethod
    def _parse(json_str: str) -> dict:
        """Helper to parse JSON responses from MinIO Admin API"""
        return json.loads(json_str)

    def user_add(self, access_key: str, secret_key: str) -> UserT:
        self.minio_admin.user_add(access_key, secret_key)
        return self._parse(self.minio_admin.user_info(access_key))

    def build_bucket_policy(self, bucket_name: str) -> PolicyT:
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetBucketLocation",
                        "s3:GetObject",
                        "s3:ListBucket",
                        "s3:PutObject",
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*",
                    ],
                }
            ],
        }
        return policy

    def policy_add(self, policy_name: str, policy: dict) -> PolicyT:
        self.minio_admin.policy_add(policy_name=policy_name, policy=policy)
        r = self.minio_admin.policy_info(policy_name=policy_name)
        return self._parse(r)

    def user_policy_set(self, policy_name: str, user: str) -> UserT:
        self.minio_admin.policy_set(policy_name=policy_name, user=user)
        r = self.minio_admin.user_info(access_key=user)
        return self._parse(r)

    def user_policy_unset(self, policy_name: str, user: str) -> UserT:
        self.minio_admin.policy_unset(policy_name=policy_name, user=user)
        r = self.minio_admin.user_info(access_key=user)
        return self._parse(r)

    def get_policy_entities(
        self, users: list[str] = [], groups: list[str] = [], policies: list[str] = []
    ) -> PolicyEntitiesT:
        r = self.minio_admin.get_policy_entities(
            users=users, groups=groups, policies=policies
        )
        return self._parse(r)

    def add_service_account(self, access_key: str) -> ServiceAccountT:
        r = self.minio_admin.add_service_account()
        return self._parse(r)

    def get_bucket_quota(self, bucket_name: str) -> BucketQuotaT:
        r = self.minio_admin.bucket_quota_get(bucket_name=bucket_name)
        return self._parse(r)

    def set_bucket_quota(self, bucket_name: str, size: int) -> BucketQuotaT:
        self.minio_admin.bucket_quota_set(bucket_name=bucket_name, size=size)
        return self.get_bucket_quota(bucket_name=bucket_name)

    def info(self) -> dict:
        r = self.minio_admin.info()
        return self._parse(r)
