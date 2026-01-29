from __future__ import annotations

import logging
from urllib.parse import urlparse

from timeio.grafana.api import TimeioGrafanaApi
from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.crypto import decrypt, get_crypt_key
from timeio.typehints import MqttPayload
from typing import TypedDict, Any

logger = logging.getLogger("grafana-dashboard-setup")


class CreateThingInGrafanaHandler(AbstractHandler):
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

        self.api = TimeioGrafanaApi.from_url(
            url=get_envvar("GRAFANA_URL"),
            credential=(
                get_envvar("GRAFANA_USER"),
                get_envvar("GRAFANA_PASSWORD"),
            ),
        )
        # needed when defining new datasource
        self.sslmode = get_envvar("GRAFANA_DEFAULT_DATASOURCE_SSLMODE")
        self.configdb_dsn = get_envvar("CONFIGDB_DSN")

    def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.configdb_dsn)
        org = self.api.t.org.get_by_name(thing.project.name)
        if org is None:
            org = self.api.t.org.create(thing.project.name)

        # create datasource, folder, dashboard in project org
        # Give Grafana and Org Admins admin access to folder
        # Give Role Editor edit access to folder
        self.create_all_in_org(thing, org_id=org["id"], role=2)

        # create team, datasource, folder, dashboard in Main org
        # Give Team viewer access to folder
        self.create_all_in_org(thing, org_id=1, role=1)

    def create_all_in_org(self, thing, org_id, role):
        p_name = thing.project.name
        p_uuid = thing.project.uuid
        self.api.organizations.switch_organization(org_id)
        if (ds := self.api.t.dsrc.get_by_uid(p_uuid)) is None:
            ds = self.api.t.dsrc.create(thing, user_prefix="grf_", sslmode=self.sslmode)

        if (team_name := self.api.t.team.get_by_name(p_name)) is None and org_id == 1:
            # only create team in Main org
            team_name = self.api.t.team.create(p_name, org_id)

        if (folder := self.api.t.fldr.get_by_uid(p_uuid)) is None:
            folder = self.api.t.fldr.create(p_name, p_uuid)

        self.api.t.fldr.set_permissions(folder, team_name, role)

        dashboard = self.api.t.dash.build(thing, folder, ds)
        geomap = self.api.t.map.build(thing, folder, ds)
        self.api.t.dash.upsert(dashboard)
        self.api.t.map.upsert(geomap)


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInGrafanaHandler().run_loop()
