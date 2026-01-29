from __future__ import annotations

from timeio.grafana.typehints import DatasourceT, FolderT
from typing import TYPE_CHECKING
from uuid import uuid5, UUID

from timeio.grafana.utils import _exists
from timeio.thing import Thing
from timeio.grafana.utils import logger

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi


class GrafanaMapDashboard:
    def __init__(self, api: TimeioGrafanaApi) -> None:
        self.api = api

    def _exists(self, uid: str) -> bool:
        return _exists(self.api.dashboard.get_dashboard, uid)

    def upsert(self, dashboard: dict) -> dict:
        """Create or update the dashboard"""
        dashboard_uid = dashboard["dashboard"]["uid"]
        dashboard_title = dashboard["dashboard"]["title"]
        action = "Updated" if self._exists(dashboard_uid) else "Created new"
        self.api.dashboard.update_dashboard(dashboard)
        logger.debug(f"{action} dashboard '{dashboard_title}'")
        return self.api.dashboard.get_dashboard(dashboard_uid)

    def build(self, thing: Thing, folder: FolderT, datasource: DatasourceT) -> dict:
        dashboard_title = "STA Locations"
        dashboard_uid = str(uuid5(UUID(thing.project.uuid), dashboard_title))
        dashboard = {
            "editable": True,
            "panels": [
                self._locations_panel(datasource),
            ],
            "tags": [folder["title"], dashboard_title, "time.IO automation"],
            "title": dashboard_title,
            "uid": dashboard_uid,
        }
        return {
            "dashboard": dashboard,
            "folderUid": folder["uid"],
            "message": "Created by time.IO",
            "overwrite": True,
        }

    def _locations_panel(self, datasource: DatasourceT) -> dict:
        return {
            "datasource": datasource,
            "gridPos": {"h": 16, "w": 24, "x": 0, "y": 0},
            "targets": [
                self._locations_query_target(datasource),
            ],
            "type": "geomap",
            "options": {
                "view": {
                    "id": "fit",
                    "zoom": 15,
                },
                "basemap": {
                    "type": "xyz",
                },
            },
        }

    @classmethod
    def _locations_query_target(cls, datasource: DatasourceT) -> dict:
        with open("timeio/grafana/sql/locations.sql", "r") as f:
            sql = f.read()
        return {
            "datasource": datasource,
            "editorMode": "code",
            "format": "table",
            "rawQuery": True,
            "rawSql": sql,
            "refId": "A",
        }
