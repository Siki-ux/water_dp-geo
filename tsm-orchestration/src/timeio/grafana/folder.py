from __future__ import annotations

from typing import TYPE_CHECKING
from timeio.grafana.typehints import FolderT
from timeio.grafana.utils import get_dict_by_key_value, _exists

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi

from timeio.grafana.utils import logger


class GrafanaFolder:
    def __init__(self, api: TimeioGrafanaApi) -> None:
        self.api = api

    def _exists(self, uid: str) -> bool:
        return _exists(self.api.folder.get_folder, uid)

    def get_by_uid(self, uid: str) -> FolderT | None:
        folders = self.api.folder.get_all_folders()
        return get_dict_by_key_value(folders, "uid", uid)

    def get_by_name(self, name: str) -> FolderT | None:
        folders = self.api.folder.get_all_folders()
        return get_dict_by_key_value(folders, "name", name)

    def create(self, name: str, uid: str) -> FolderT:
        folder = self.api.folder.create_folder(title=name, uid=uid)
        logger.debug(f"Created new folder '{name}'")
        return self.get_by_uid(uid)

    def set_permissions(self, folder, team, role):
        if role == 1:
            # set GRAFANA_USER as folder admin and team as Viewer
            permissions = {
                "items": [
                    {"userId": 1, "permission": 4},
                    {"teamId": team["id"], "permission": 1},
                ]
            }
        else:
            # allow role Editor to edit folder
            permissions = {
                "items": [
                    {"userId": 1, "permission": 4},
                    {"role": "Admin", "permission": 4},
                    {"role": "Editor", "permission": role},
                ]
            }
        self.api.folder.update_folder_permissions(folder["uid"], permissions)
        logger.debug(f"Set permissions on folder '{folder['title']}' for role '{role}'")
