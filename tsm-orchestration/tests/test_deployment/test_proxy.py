#!/usr/bin/env python3

import os
import requests
import pytest

from dotenv import load_dotenv

load_dotenv()

ENV_KEYS = [
    "PROXY_URL",
    "OBJECT_STORAGE_BROWSER_REDIRECT_URL",
    "VISUALIZATION_PROXY_URL",
    "STA_PROXY_URL",
    "THING_MANAGEMENT_LEGACY_PROXY_URL",
]


def get_env_endpoints():
    env_endpoints = [os.environ.get(env_var) for env_var in ENV_KEYS]
    return env_endpoints


@pytest.mark.parametrize("endpoint", get_env_endpoints())
def test_proxy_endpoints(endpoint):
    response = requests.get(endpoint, timeout=5)
    response.raise_for_status()
