from __future__ import annotations

from typing import TypedDict, Any


class TeamT(TypedDict):
    id: int
    uid: str
    orgId: int
    name: str
    email: str
    avatarUrl: str
    memberCount: int
    permission: int
    accessControl: Any


class OrgT(TypedDict):
    id: int
    name: str
    address: dict[str, str]


class FolderT(TypedDict):
    id: int
    uid: str
    orgId: int
    title: str
    url: str
    hasAcl: bool
    canSave: bool
    canEdit: bool
    canAdmin: bool
    canDelete: bool
    createdBy: str
    created: str
    updatedBy: str
    updated: str
    version: int


class DatasourceT(TypedDict):
    id: int
    uid: str
    orgId: int
    name: str
    type: str
    typeName: str
    typeLogoUrl: str
    access: str
    url: str
    user: str
    database: str
    basicAuth: bool
    isDefault: bool
    jsonData: dict[str, Any]
    readOnly: bool


class UserT(TypedDict):
    id: int
    uid: str
    email: str
    name: str
    login: str
    theme: str
    orgId: int
    isGrafanaAdmin: bool
    isDisabled: bool
    isExternal: bool
    isExternallySynced: bool
    isGrafanaAdminExternallySynced: bool
    authLabels: Any
    updatedAt: str
    createdAt: str
    avatarUrl: str
