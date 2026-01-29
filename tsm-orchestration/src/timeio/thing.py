from __future__ import annotations

from timeio import frost


class Database:
    def __init__(
        self,
        username: str,
        password: str,
        url: str,
        ro_username: str,
        ro_password: str,
        ro_url: str,
    ):
        self.username = username
        self.password = password
        self.url = url
        self.ro_username = ro_username
        self.ro_password = ro_password
        self.ro_url = ro_url

    @classmethod
    def get_instance(cls, message: dict) -> Database:
        try:
            return cls(
                message["username"],
                message["password"],
                message["url"],
                message["ro_username"],
                message["ro_password"],
                message["ro_url"],
            )
        except KeyError as e:
            raise ValueError(
                f'Unable to get Database instance from message "{message}"'
            ) from e


class Project:
    def __init__(self, uuid: str, name: str) -> None:
        self.uuid = uuid
        self.name = name

    @classmethod
    def get_instance(cls, message: dict) -> Project:
        try:
            return cls(message["uuid"], message["name"])
        except KeyError as e:
            raise ValueError(
                f'Unable to get Project instance from message "{message}"'
            ) from e


class RawDataStorage:
    def __init__(
        self,
        username: str,
        password: str,
        bucket_name: str,
        filename_pattern: str | None = None,
    ):
        self.username = username
        self.password = password
        self.bucket_name = bucket_name
        self.filename_pattern = filename_pattern

    @classmethod
    def get_instance(cls, message: dict) -> RawDataStorage:
        try:
            return cls(
                message["username"],
                message["password"],
                message["bucket_name"],
                message.get("filename_pattern", None),
            )
        except KeyError as e:
            raise ValueError(
                f'Unable to get RawDataStorage instance from message "{message}"'
            ) from e


class ExternalSFTP:
    def __init__(
        self,
        enabled: bool,
        uri: str,
        path: str,
        username: str,
        password: str,
        sync_interval: int,
        public_key: str,
        private_key_path: str,
    ):
        self.enabled = enabled
        self.uri = uri
        self.path = path
        self.username = username
        self.password = password
        self.sync_interval = sync_interval
        self.public_key = public_key
        self.private_key_path = private_key_path

    @classmethod
    def get_instance(cls, message: dict) -> ExternalSFTP:
        try:
            return cls(
                message["enabled"],
                message["uri"],
                message["path"],
                message["username"],
                message["password"],
                message["sync_interval"],
                message["public_key"],
                message["private_key_path"],
            )
        except KeyError as e:
            raise ValueError(
                f'Unable to get ExternalSFTP instance from message "{message}"'
            ) from e


class ExternalApi:
    def __init__(
        self, enabled: bool, api_type: str, sync_interval: int, settings: dict
    ):
        self.enabled = enabled
        self.api_type_name = api_type
        self.sync_interval = sync_interval
        self.settings = settings

    @classmethod
    def get_instance(cls, message: dict) -> ExternalApi:
        try:
            return cls(
                message["enabled"],
                message["type"],
                message["sync_interval"],
                message["settings"],
            )
        except KeyError as e:
            raise ValueError(
                f'Unable to get ExternalAPI instance from message "{message}"'
            ) from e


class Thing:
    def __init__(
        self,
        uuid: str,
        name: str | None = None,
        project: Project | None = None,
        database: Database | None = None,
        raw_data_storage: RawDataStorage | None = None,
        external_sftp: ExternalSFTP | None = None,
        external_api: ExternalApi | None = None,
        description: str | None = None,
        properties: dict | None = None,
    ):
        self.uuid = uuid
        self.name = name
        self.project = project
        self.database = database
        self.raw_data_storage = raw_data_storage
        self.external_sftp = external_sftp
        self.external_api = external_api
        self.description = description
        self.properties = properties

    @classmethod
    def get_instance(cls, message: dict) -> Thing:
        try:
            # external sftp and/or external api is optional
            external_sftp = None
            if "ext_sftp_settings" in message:
                external_sftp = ExternalSFTP.get_instance(message["ext_sftp_settings"])
            external_api = None
            if "ext_api_settings" in message:
                external_api = ExternalApi.get_instance(message["ext_api_settings"])

            return cls(
                message["uuid"],
                message["name"],
                Project.get_instance(message["project"]),
                Database.get_instance(message["database"]),
                RawDataStorage.get_instance(message["raw_data_storage"]),
                external_sftp,
                external_api,
                message["description"],
                message["properties"],
            )
        except KeyError as e:
            raise ValueError(
                f'Unable to get Thing instance from message "{message}"'
            ) from e

    def setup_frost(self, tomcat_proxy_url: str):
        frost.write_context_file(
            schema=self.database.username.lower(),
            user=f"sta_{self.database.ro_username.lower()}",
            password=self.database.ro_password,
            db_url=self.database.url,
            tomcat_proxy_url=tomcat_proxy_url,
        )
