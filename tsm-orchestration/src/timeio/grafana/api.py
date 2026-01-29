from __future__ import annotations

from grafana_client import GrafanaApi
from types import SimpleNamespace

from timeio.grafana.organization import GrafanaOrganization
from timeio.grafana.team import GrafanaTeam
from timeio.grafana.folder import GrafanaFolder
from timeio.grafana.datasource import GrafanaDatasource
from timeio.grafana.dashboard import GrafanaDashboard
from timeio.grafana.geomap import GrafanaMapDashboard
from timeio.grafana.user import GrafanaUser
from timeio.grafana.utils import logger


class TimeioGrafanaApi(GrafanaApi):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.t = SimpleNamespace()
        self.t.org = GrafanaOrganization(self)
        self.t.team = GrafanaTeam(self)
        self.t.fldr = GrafanaFolder(self)
        self.t.dsrc = GrafanaDatasource(self)
        self.t.dash = GrafanaDashboard(self)
        self.t.map = GrafanaMapDashboard(self)
        self.t.user = GrafanaUser(self)

    @classmethod
    def connect_from_url(
        cls, url: str, credential: tuple[str, str]
    ) -> TimeioGrafanaApi:
        return super().from_url(url=url, credential=credential)
