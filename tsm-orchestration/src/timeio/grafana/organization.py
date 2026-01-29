from __future__ import annotations

from typing import TYPE_CHECKING
from timeio.grafana.typehints import OrgT
from timeio.grafana.utils import get_dict_by_key_value, logger

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi


class GrafanaOrganization:
    def __init__(self, api: TimeioGrafanaApi) -> None:
        self.api = api

    def _get_org(self, key: str, value: str | int):
        orgs = self.api.organizations.list_organization()
        org = get_dict_by_key_value(orgs, key, value)
        return org

    def get_by_id(self, id: int) -> OrgT | None:
        return self._get_org("id", id)

    def get_by_name(self, name: str) -> OrgT | None:
        return self._get_org("name", name)

    def get_names_and_ids(self) -> list[dict[str, int]]:
        """
        Get all organization names and their IDs in Grafana.
        """
        orgs = self.api.organizations.list_organization()
        return {org.get("name"): org.get("id") for org in orgs}

    def create(self, name: str) -> OrgT:
        if not self.get_by_name(name):
            self.api.organization.create_organization({"name": name})
            logger.debug(f"Created new organization '{name}'")
        else:
            logger.debug(f"Organization '{name}' already exists")
        return self.get_by_name(name)
