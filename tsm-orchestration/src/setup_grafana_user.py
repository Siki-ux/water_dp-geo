from __future__ import annotations

import logging
import re
import time
from typing import Literal

from timeio.grafana.api import TimeioGrafanaApi
from grafana_client.client import GrafanaException

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.common import get_envvar, setup_logging

logger = logging.getLogger("grafana-user-setup")


class CreateGrafanaUserHandler(AbstractHandler):

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
        self.vo_group_key = get_envvar("VO_GROUP_KEY", "eduperson_entitlement")
        self.vo_login_key = get_envvar("VO_LOGIN_KEY", "eduperson_principal_name")
        # if true, vo group admins become grafana organization admins,
        # otherwise, they become editors
        self.gf_roles_from_vo_roles = get_envvar(
            "GF_ROLE_FROM_VO_ROLE", False, cast_to=bool
        )
        self.vo_admin_subgroup = get_envvar("VO_ADMIN_SUBGROUP", "ufz-sms-admin")
        self.allowed_vos = get_envvar("ALLOWED_VOS")

    def act(self, content: dict, message: MQTTMessage):
        user_name = content.get(self.vo_login_key)
        vo_groups = content.get(self.vo_group_key)
        if user_id := self.api.t.user.get_id(user_name):
            logger.debug(f"Found user {user_name} with user_id {user_id}")
            gf_groups = self.map_vo_groups_to_gf_orgs(vo_groups)
            self.api.t.user.update_orgs(user_id, user_name, gf_groups)
        else:
            logger.warning(f"Could not find user {user_name}. Skipping user sync.")

    def map_vo_groups_to_gf_orgs(
        self, vo_groups
    ) -> dict[str, Literal["Admin", "Editor"]]:
        """Translate VO groups to grafana groups."""
        orgs = {}
        allowed_vos = "|".join(self.allowed_vos.split(","))

        # match.group(1): the VO  (e.g. UFZ-Timeseries-Management) or None
        # match.group(2): the VO group  (e.g. DemoGroup)
        # match.group(3): VO_ADMIN_SUBGROUP with colon (e.g. :ufz-sms-admin) or None if not present
        # match.group(4): VO_ADMIN_SUBGROUP without colon (e.g. ufz-sms-admin) or None if not present
        pattern = rf"({allowed_vos}):([^:#]+)(:({self.vo_admin_subgroup or ''}))?"

        for vo_group in vo_groups:
            admin = org_name = role = None
            if match := re.search(pattern, vo_group):
                org_name = f"{match.group(1)}:{match.group(2)}"
                admin = match.group(4)
                role: Literal["Admin", "Editor"] = "Editor"
                if admin and self.gf_roles_from_vo_roles:
                    role = "Admin"
                orgs[org_name] = role

            logger.debug(
                "vo_group: %s\nvo_admin_subgroup: %s\ngf_org: %s\ngf_role: %s\n",
                *(vo_group, admin, org_name, role),
            )
        return orgs


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateGrafanaUserHandler().run_loop()
