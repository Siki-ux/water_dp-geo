from __future__ import annotations
from typing import TypedDict


class UserT(TypedDict):
    status: str
    updatedAt: str
    policyName: str | None


class PolicyStatementT(TypedDict):
    Effect: str
    Action: list[str]
    Resource: str


class PolicyT(TypedDict):
    Version: str
    Statement: list[PolicyStatementT]


class PolicyEntitiesT(TypedDict):
    timestamp: str
    userMappings: list[dict] | None
    groupMappings: list[dict] | None
    policyMappings: list[dict] | None


class ServiceAccountCredentialsT(TypedDict):
    accessKey: str
    secretKey: str
    expiration: str


class ServiceAccountT(TypedDict):
    credentials: ServiceAccountCredentialsT


class BucketQuotaT(TypedDict):
    quota: int
    size: int
    rate: int
    requests: int
    quotatype: str
