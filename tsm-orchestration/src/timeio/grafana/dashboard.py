from __future__ import annotations

from timeio.grafana.typehints import DatasourceT, FolderT
from typing import TYPE_CHECKING

from timeio.grafana.utils import _exists
from timeio.thing import Thing
from timeio.grafana.utils import logger

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi


class GrafanaDashboard:
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
        dashboard_uid = thing.uuid
        dashboard_title = thing.name
        dashboard = {
            "editable": True,
            "liveNow": True,
            "panels": [
                self._journal_panel(thing, datasource),
                self._observations_row_panel(),
                self._observation_panel(thing, datasource),
            ],
            "refresh": False,
            "tags": [folder["title"], dashboard_title, "time.IO automation"],
            "templating": {
                "list": [
                    self._datastream_templating(thing, datasource),
                    self._show_qaqc_templating(datasource),
                ]
            },
            "time": {"from": "now-7d", "to": "now"},
            "title": dashboard_title,
            "uid": dashboard_uid,
        }
        return {
            "dashboard": dashboard,
            "folderUid": folder["uid"],
            "message": "Created by time.IO",
            "overwrite": True,
        }

    def _datastream_templating(self, thing, datasource) -> dict:
        return {
            "datasource": datasource,
            "hide": 0,
            "includeAll": True,
            "label": "Datastream",
            "multi": True,
            "name": "datastream_pos",
            "query": self._datastream_sql(thing.uuid),
            "refresh": 1,
            "sort": 7,
            "type": "query",
        }

    @staticmethod
    def _show_qaqc_templating(datasource: DatasourceT) -> dict:
        return {
            "datasource": datasource,
            "hide": 0,
            "type": "custom",
            "name": "show_qaqc_flags",
            "label": "Show QAQC Flags",
            "query": "False,True",
            "multi": False,
            "includeAll": False,
            "options": [
                {"text": "False", "value": "False", "selected": True},
                {"text": "True", "value": "True", "selected": False},
            ],
        }

    def _observation_panel(self, thing: Thing, datasource: DatasourceT) -> dict:
        return {
            "datasource": datasource,
            "gridPos": {"h": 8},
            "options": {
                "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": False,
                }
            },
            "maxPerRow": 3,
            "repeat": "datastream_pos",
            "repeatDirection": "h",
            "fieldConfig": {
                "overrides": [self._show_qaqc_overrides()],
            },
            "targets": [
                self._observation_query_target(thing, datasource),
                self._qaqc_query_target(thing, datasource),
            ],
            "title": "$datastream_pos",
            "type": "timeseries",
        }

    @classmethod
    def _observation_query_target(cls, thing: ThingT, datasource: DatasourceT) -> dict:
        return {
            "datasource": datasource,
            "editorMode": "code",
            "format": "time_series",
            "rawQuery": True,
            "rawSql": cls._observation_sql(thing.uuid),
            "refId": "A",
        }

    @classmethod
    def _qaqc_query_target(cls, thing: ThingT, datasource: DatasourceT) -> dict:
        return {
            "datasource": datasource,
            "editorMode": "code",
            "format": "time_series",
            "rawQuery": True,
            "rawSql": cls._qaqc_sql(thing.uuid),
            "refId": "B",
        }

    @staticmethod
    def _show_qaqc_overrides() -> dict:
        return {
            "matcher": {
                "id": "byFrameRefID",
                "options": "B",
            },
            "properties": [
                {"id": "custom.drawStyle", "value": "points"},
                {"id": "custom.axisPlacement", "value": "hidden"},
                {"id": "custom.axisSoftMax", "value": 1},
                {"id": "custom.pointSize", "value": 7},
            ],
        }

    @staticmethod
    def _observations_row_panel() -> dict:
        return {
            "collapsed": False,
            "gridPos": {"h": 1, "w": 24},
            "panels": [],
            "title": "Observations",
            "type": "row",
        }

    def _journal_panel(self, thing: Thing, datasource: dict[str, str]):
        return {
            "collapsed": True,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
            "panels": [self._journal_table(thing, datasource)],
            "title": "Status Journal",
            "type": "row",
        }

    def _journal_table(self, thing: Thing, datasource: dict[str, str]):
        """Create the journal table"""
        return {
            "type": "table",
            "title": "Status Journal",
            "gridPos": {"h": 12, "w": 24},
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "filterable": True,
                    },
                    "mappings": [
                        {
                            "options": {
                                "ERROR": {"color": "#9d545d", "index": 2},
                                "INFO": {"color": "#6d9967", "index": 0},
                                "WARNING": {"color": "#b48250", "index": 1},
                            },
                            "type": "value",
                        }
                    ],
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "level"},
                        "properties": [
                            {
                                "id": "custom.cellOptions",
                                "value": {
                                    "applyToRow": True,
                                    "mode": "gradient",
                                    "type": "color-background",
                                },
                            }
                        ],
                    }
                ],
            },
            "transparent": True,
            "targets": [
                {
                    "datasource": datasource,
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": self._journal_sql(thing.uuid),  # get from sql/journal.sql
                    "refId": "A",
                }
            ],
            "datasource": datasource,
        }

    # SQL Queries
    @staticmethod
    def _datastream_sql(uuid: str) -> str:
        with open("timeio/grafana/sql/datastream.sql", "r") as f:
            sql = f.read().format(uuid=uuid)
        return sql

    @staticmethod
    def _journal_sql(uuid: str) -> str:
        with open("timeio/grafana/sql/journal.sql", "r") as f:
            sql = f.read().format(uuid=uuid)
        return sql

    @staticmethod
    def _observation_sql(uuid: str) -> str:
        with open("timeio/grafana/sql/observation.sql", "r") as f:
            sql = f.read().format(uuid=uuid)
        return sql

    @staticmethod
    def _qaqc_sql(uuid: str) -> str:
        with open("timeio/grafana/sql/qaqc.sql", "r") as f:
            sql = f.read().format(uuid=uuid)
        return sql
