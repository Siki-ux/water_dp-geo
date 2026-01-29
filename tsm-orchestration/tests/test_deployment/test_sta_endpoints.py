#!/usr/bin/env python3

from __future__ import annotations
import requests
import os
import psycopg
import pytest

from test_deployment import LOCAL_DEV
from dotenv import load_dotenv

load_dotenv()
sta_base_url = os.environ.get("STA_PROXY_URL")
configdb_dsn = os.environ.get("CONFIGDB_READONLY_DSN")
if LOCAL_DEV:
    configdb_dsn = configdb_dsn.replace("database", "localhost")


def get_all_projects():
    with psycopg.connect(configdb_dsn) as conn:
        rows = conn.execute('SELECT "schema" from "database"').fetchall()
    return [row[0] for row in rows]


sta_endpoints = [
    "Things",
    "Sensors",
    "ObservedProperties",
    "Observations",
    "Locations",
    "HistoricalLocations",
    "FeaturesOfInterest",
    "Datastreams",
]


@pytest.mark.parametrize("project", get_all_projects())
@pytest.mark.parametrize("endpoint", sta_endpoints)
def test_sta_for_all_projects(project, endpoint):
    url = f"{sta_base_url}{project}/v1.1/{endpoint}"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
