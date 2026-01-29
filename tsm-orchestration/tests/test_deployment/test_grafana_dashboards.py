#!/usr/bin/env python3

from __future__ import annotations
import os
from typing import Any

import pytest
from dotenv import load_dotenv
from grafana_client import GrafanaApi
import psycopg
from typing import Generator
from test_deployment import LOCAL_DEV

load_dotenv()

CONFIGDB_DSN = os.environ.get("CONFIGDB_READONLY_DSN")
if LOCAL_DEV:
    CONFIGDB_DSN = CONFIGDB_DSN.replace("database", "localhost")


def unpack(collection: list[tuple[Any]]) -> list[Any]:
    return [obj[0] for obj in collection]


@pytest.fixture(scope="module")
def db() -> Generator[psycopg.Connection]:
    with psycopg.connect(CONFIGDB_DSN) as conn:
        yield conn


def test_db(db):
    db.execute("")


@pytest.fixture(scope="module")
def api() -> GrafanaApi:
    return GrafanaApi.from_url(
        url=os.environ.get("VISUALIZATION_PROXY_URL"),
        credential=(
            os.environ.get("VISUALIZATION_USER"),
            os.environ.get("VISUALIZATION_PASSWORD"),
        ),
    )


def test_api(api):
    # Since grafana_client version 5.0, api.health does not query the
    # /health endpoint anymore, so we do it manually, which should works
    # for all versions.
    assert api.client.GET("/health").get("database") == "ok"


@pytest.fixture(scope="module")
def thing_uuids(db: psycopg.Connection) -> list[str]:
    return unpack(db.execute("select distinct uuid::varchar from thing").fetchall())


@pytest.fixture(scope="module")
def project_names(db: psycopg.Connection) -> list[str]:
    return unpack(db.execute("select distinct name from project").fetchall())


@pytest.fixture(scope="module")
def organisations(api: GrafanaApi) -> list[dict[str, Any]]:
    # ignore the `Main Org.` which is always first.
    return api.organizations.list_organization()[1:]


def test_organisations(project_names, organisations):
    """Check if we have an organisation for each time.IO project"""
    missing = set(project_names) - set(o["name"] for o in organisations)
    assert missing == set()


def test_main_org_dashboards(api, thing_uuids):
    """Check if we have a dashboard for each time.IO thing in the `Main Org.`"""
    api.organizations.switch_organization(1)
    dashboards = api.search.search_dashboards(type_="dash-db")
    missing = set(thing_uuids) - set(d["uid"] for d in dashboards)
    assert missing == set()


def _get_things(db: psycopg.Connection, project_name):
    q = (
        "select distinct t.uuid::varchar from thing t "
        "join project p on p.id = t.project_id where p.name = %s"
    )
    return unpack(db.execute(q, [project_name]).fetchall())


def test_dashboards(
    subtests, db, api: GrafanaApi, project_names, organisations, thing_uuids
):
    """Test if each organisation (project)  has a dashboard for each thing."""
    for org in organisations:
        if (name := org["name"]) not in project_names:
            continue
        uuids = _get_things(db, name)
        api.organizations.switch_organization(org["id"])
        dashboards = api.search.search_dashboards(type_="dash-db")
        with subtests.test(msg="test if each thing has a dashboard", org=name):
            missing = set(uuids) - set(d["uid"] for d in dashboards)
            assert missing == set()
