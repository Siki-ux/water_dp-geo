from __future__ import annotations

from typing import TYPE_CHECKING

from timeio.grafana.typehints import DatasourceT
from timeio.grafana.utils import get_dict_by_key_value, _exists
from timeio.thing import Thing
from timeio.crypto import decrypt, get_crypt_key
from urllib.parse import urlparse
from timeio.grafana.utils import logger

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi


class GrafanaDatasource:
    def __init__(self, api: TimeioGrafanaApi) -> None:
        self.api = api

    def exists(self, uuid) -> bool:
        return _exists(self.api.datasource.get_datasource_by_uid, uuid)

    def _get_datasource(self, key: str, value: str | int):
        datasources = self.api.datasource.list_datasources()
        ds = get_dict_by_key_value(datasources, key, value)
        return ds

    def get_by_uid(self, uid: str) -> DatasourceT | None:
        return self._get_datasource("uid", uid)

    def get_by_name(self, name: str) -> DatasourceT | None:
        return self._get_datasource("name", name)

    def create(
        self, thing: Thing, user_prefix: str, sslmode: str = "disable"
    ) -> DatasourceT:
        db_user = user_prefix + thing.database.ro_username
        db_pass = decrypt(thing.database.ro_password, get_crypt_key())
        db_url_parsed = urlparse(thing.database.url)
        db_path = db_url_parsed.path.lstrip("/")
        db_url = db_url_parsed.hostname
        if db_url_parsed.port is not None:  # only add port, if it is defined
            db_url += f":{db_url_parsed.port}"
        datasource = {
            "name": thing.project.name,
            "uid": thing.project.uuid,
            "type": "postgres",
            "url": db_url,
            "user": db_user,
            "access": "proxy",
            "basicAuth": False,
            "jsonData": {
                "database": db_path,
                "sslmode": sslmode,
                "timescaledb": False,
            },
            "secureJsonData": {"password": db_pass},
        }
        self.api.datasource.create_datasource(datasource)
        logger.debug(f"Created new datasource '{datasource['name']}'")
        return self.get_by_name(thing.project.name)
