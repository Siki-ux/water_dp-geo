from __future__ import annotations

from typing import TYPE_CHECKING
import time

from timeio.grafana.utils import _exists, logger
from grafana_client.client import GrafanaException

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi


class GrafanaUser:
    def __init__(self, api: TimeioGrafanaApi) -> None:
        self.api = api

    def _exists(self, name: str) -> bool:
        return _exists(self.api.users.find_user, name)

    def get_id(self, name, max_tries: int = 5, sleep: int = 2) -> int | None:
        """
        Get the user ID by name, retrying if necessary.
        """
        for cnt in range(max_tries):
            try:
                return self.api.users.find_user(name).get("id")
            except GrafanaException:
                if cnt < max_tries - 1:
                    logger.debug(f"Fetching user {name!r} failed. Retrying...")
                time.sleep(sleep)
        return None

    def get_orgs(self, user_id: int) -> dict[str, str]:
        """
        Get the organizations the user is part of.
        Returns a dictionary with organization names as keys and roles as values.
        """
        orgs = self.api.users.get_user_organisations(user_id)
        return {org.get("name"): org.get("role") for org in orgs}

    def add_to_org(self, role: str, login_name: str) -> None:
        """
        Add a user to an organization with the specified role.
        """
        user = {"role": role, "loginOrEmail": login_name}
        self.api.organization.add_user_current_organization(user)

    def remove_from_org(self, user_id) -> None:
        """
        Remove the user from the current organization.
        """
        self.api.organization.delete_user_from_current_organization(user_id)

    def is_in_team(self, team_id: int, user_id: int) -> bool:
        """
        Check if the user is part of the specified team.
        """
        teams = self.api.users.get_user_teams(user_id)
        return any(team.get("id") == team_id for team in teams)

    def add_to_team(self, org_name: str, user_id: int) -> None:
        team_id = self.api.t.team.get_id_by_name(org_name)
        if team_id and not self.is_in_team(team_id, user_id):
            self.api.teams.add_team_member(team_id, user_id)

    def remove_from_team(self, org_name: str, user_id: int) -> None:
        team_id = self.api.t.team.get_id_by_name(org_name)
        if team_id and self.is_in_team(team_id, user_id):
            self.api.teams.remove_team_member(team_id, user_id)

    def update_orgs(
        self, user_id: int, user_name: str, new_orgs: dict[str, str]
    ) -> None:
        """
        Update the user's organizations based on the provided dictionary.
        Adds, updates, or removes the user from organizations as necessary.
        """
        old_orgs = self.get_orgs(user_id)
        user_add_orgs = new_orgs.keys() - old_orgs.keys()
        user_update_orgs = old_orgs.keys() & new_orgs.keys()
        user_delete_orgs = old_orgs.keys() - new_orgs.keys() - {"Main Org."}

        # todo: should we also really create new orgs that
        #  was never seen before? then we must also iterate
        #  over create_org_names outside this loop.

        # no, we don't want to create org names that don't yet exist in grafana
        # creating the orgs should be done by the grafana_dashboard_setup.py

        all_orgs = self.api.t.org.get_names_and_ids()
        all_orgs.pop("Main Org.", None)
        # We iterate over all orgs in Grafana and add/update/delete user in respective org
        for org, org_id in all_orgs.items():
            self.api.organizations.switch_organization(org_id)
            new_role = new_orgs.get(org)
            old_role = old_orgs.get(org)
            if org in user_add_orgs:
                logger.debug(f"Add user to org. U=%s, O=%s", user_name, org)
                self.add_to_org(new_role, user_name)
                self.api.organizations.switch_organization(1)
                self.add_to_team(org, user_id)
            elif org in user_update_orgs:
                if new_role != old_role:
                    logger.debug(
                        f"Update user. U=%s, O=%s, R=%s", user_name, org, new_role
                    )
                    # grafana: "cannot change role for externally synced user"
                    # so we have to delete and re-add the user
                    self.remove_from_org(user_id)
                    self.add_to_org(new_role, user_name)
                self.api.organizations.switch_organization(1)
                if not self.is_in_team(org_id, user_id):
                    self.add_to_team(org, user_id)
            elif org in user_delete_orgs:
                logger.debug(f"Remove user from org. U=%s, O=%s", user_name, org)
                self.remove_from_org(user_id)
                self.api.organizations.switch_organization(1)
                self.remove_from_team(org, user_id)
