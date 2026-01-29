#!/usr/bin/env python3
from __future__ import annotations
import socket
from functools import lru_cache, partial
from typing import TypedDict, Generator

import pytest
import dotenv
import paramiko
import psycopg
from psycopg.rows import dict_row
from ftplib import FTP, FTP_TLS
from minio import Minio
import timeio.crypto
from timeio.common import get_envvar
from test_deployment import LOCAL_DEV

if not dotenv.load_dotenv():
    raise EnvironmentError("No .env file found")


DECRYPT_KEY = timeio.crypto.get_crypt_key()
DATA_QUERY = (
    'select t.uuid, it.name as "ingest_type", s3."user", s3.password, s3.bucket '
    "from config_db.thing t "
    "left outer join config_db.ingest_type it on t.ingest_type_id = it.id "
    "left outer join config_db.s3_store s3 on t.s3_store_id = s3.id"
)


class ThingDataT(TypedDict):
    uuid: str  # thing uuid
    ingest_type: str  # ingest type of the thing
    user: None | str  # S3 user
    password: None | str  # S3 password
    bucket: None | str  # S3 bucket name


@pytest.fixture(scope="module")
def minio_cl():
    host = get_envvar("OBJECT_STORAGE_HOST")
    if LOCAL_DEV:
        host = host.replace("object-storage", "localhost")
    yield Minio(
        endpoint=host,
        access_key=get_envvar("OBJECT_STORAGE_ROOT_USER"),
        secret_key=get_envvar("OBJECT_STORAGE_ROOT_PASSWORD"),
        secure=get_envvar("OBJECT_STORAGE_SECURE", cast_to=bool),
    )


@pytest.fixture()
def ftp() -> Generator[FTP]:
    host = get_envvar("OBJECT_STORAGE_FTP_PORT")
    host, port = host.split(":")
    with FTP() as ftp:
        ftp.connect(host=host, port=int(port), timeout=5)
        yield ftp


@pytest.fixture()
def ftps() -> Generator[FTP_TLS]:
    host = get_envvar("OBJECT_STORAGE_FTP_PORT")
    host, port = host.split(":")
    with FTP_TLS() as ftps:
        ftps.connect(host=host, port=int(port), timeout=5)
        ftps.auth()  # start TLS
        ftps.prot_p()  # encrypt channel
        yield ftps


@pytest.fixture()
def sftp_transport() -> Generator[paramiko.Transport]:
    host = get_envvar("OBJECT_STORAGE_SFTP_PORT")
    transport = paramiko.Transport(host)
    yield transport
    transport.close()


# Attention: This already runs at test collection/parameterization stage
@lru_cache()
def get_things() -> ThingDataT:
    dsn = get_envvar("CONFIGDB_READONLY_DSN")
    if LOCAL_DEV:
        dsn = dsn.replace("database", "localhost")

    with psycopg.connect(dsn) as conn:  # type: psycopg.Connection
        with conn.cursor(row_factory=dict_row) as cur:
            return cur.execute(DATA_QUERY).fetchall()


def decrypt(pw: str) -> str:
    return timeio.crypto.decrypt(pw, DECRYPT_KEY)


def skip_optional_s3(thing: ThingDataT):
    """Skip all thing that not necessarily have a S3 storage associated.

    Oly Things with ingest_type (ext)SFTP must have a S3 storage. Things
    with other ingest_types could have a bucket, but in most cases they
    do not have one.
    """
    if (ingest_type := thing.get("ingest_type")) not in ["sftp", "extsftp"]:
        pytest.skip(f"ingest_type {ingest_type!r} requires no S3 storage")


# ############################################################
# Tests
# ############################################################


def test_minio_connection(minio_cl):
    minio_cl.bucket_exists("abc")


@pytest.mark.parametrize("thing", get_things())
def test_user_login(thing):
    skip_optional_s3(thing)
    host = get_envvar("OBJECT_STORAGE_HOST")
    if LOCAL_DEV:
        host = host.replace("object-storage", "localhost")
    cl = Minio(
        endpoint=host,
        access_key=thing["user"],
        secret_key=decrypt(thing["password"]),
        secure=get_envvar("OBJECT_STORAGE_SECURE", cast_to=bool),
    )
    # We cannot use `Minio.bucket_exists`, because we don't
    # have the rights to ask for outside our scope.
    assert cl.list_buckets()


@pytest.mark.parametrize("thing", get_things())
def test_bucket_exists(minio_cl, thing):
    skip_optional_s3(thing)
    bucket_name = thing.get("bucket")
    uuid = str(thing.get("uuid"))
    assert minio_cl.bucket_exists(bucket_name)
    # check if uuid is reflected in bucket name
    assert uuid in bucket_name


@pytest.mark.parametrize("thing", get_things())
def test_ftp(ftp, thing):
    skip_optional_s3(thing)
    user = thing.get("user")
    passwd = decrypt(thing.get("password"))
    ftp.login(user, passwd)


@pytest.mark.parametrize("thing", get_things())
def test_ftps(ftps, thing):
    skip_optional_s3(thing)
    user = thing.get("user")
    passwd = decrypt(thing.get("password"))
    ftps.login(user=user, passwd=passwd)


@pytest.mark.parametrize("thing", get_things())
def test_sftp(sftp_transport, thing):
    skip_optional_s3(thing)
    user = thing.get("user")
    passwd = decrypt(thing.get("password"))
    sftp_transport.connect(username=user, password=passwd)
    sftp = paramiko.SFTPClient.from_transport(sftp_transport)
    sftp.close()
