from __future__ import annotations

from typing import TYPE_CHECKING

from timeio.grafana.typehints import TeamT
from timeio.grafana.utils import get_dict_by_key_value, logger

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi


class GrafanaTeam:
    def __init__(self, api: TimeioGrafanaApi) -> None:
        self.api = api

    def get_by_name(self, name: str) -> TeamT | None:
        """
        Get the team by name.
        """
        teams = self.api.teams.search_teams()
        return get_dict_by_key_value(teams, "name", name)

    def get_id_by_name(self, name: str) -> int | None:
        """
        Get the team ID by name.
        Returns None if the team does not exist.
        """
        team = self.get_by_name(name)
        return team.get("id") if team else None

    def create(self, name, org_id) -> TeamT:
        """
        Create a new team with the given name and organization ID.
        """
        res = self.api.teams.add_team({"name": name, "orgId": org_id})
        logger.debug(f"Created new team '{name}'")
        return self.get_by_name(name)
