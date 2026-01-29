#!/usr/bin/env python3
from __future__ import annotations

import abc
import logging
import os
import stat
import time
from urllib.parse import urlparse
from typing import IO, Any
from contextlib import contextmanager

import minio
from minio.datatypes import Object as MinioObject
from paramiko import (
    SSHClient,
    SFTPClient,
    SFTPAttributes,
    MissingHostKeyPolicy,
)
from paramiko.config import SSH_PORT
from timeio.journaling import Journal

journal = Journal("CronJob")
logger = logging.getLogger("sftp_sync")


class RemoteFS(abc.ABC):

    files: dict[str, Any]

    @abc.abstractmethod
    def exist(self, path: str) -> bool: ...

    @abc.abstractmethod
    def is_dir(self, path: str) -> bool: ...

    @abc.abstractmethod
    def last_modified(self, path: str) -> float: ...

    @abc.abstractmethod
    def size(self, path: str) -> int: ...

    @abc.abstractmethod
    def open(self, path: str): ...

    @abc.abstractmethod
    def put(self, path: str, fo: IO[bytes], size: int) -> None: ...

    @abc.abstractmethod
    def mkdir(self, path: str) -> None: ...

    @abc.abstractmethod
    def close(self) -> None: ...

    def update(self, other: RemoteFS, path) -> None:
        """
        Update or create a file at the same location as in the other
        file system.
        """
        if other.is_dir(path):
            raise ValueError(f"Cannot update a directory")
        if self.exist(path):
            logger.debug(f"UPDATE {path}")
        else:
            logger.debug(f"CREATE {path}")
        with other.open(path) as fo:
            self.put(path, fo, other.size(path))


class MinioFS(RemoteFS):

    cl: minio.Minio
    files: dict[str, MinioObject]

    @classmethod
    def from_credentials(
        cls,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str | None = None,
        secure: bool = True,
    ) -> MinioFS:
        cl = minio.Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        return cls(client=cl, bucket_name=bucket_name)

    def __init__(
        self,
        client: minio.Minio,
        bucket_name: str,
    ) -> None:
        self.cl = client
        self.bucket_name = bucket_name
        self._get_files()

    def _get_files(self):
        self.files = {
            file.object_name: file
            for file in self.cl.list_objects(self.bucket_name, recursive=True)
        }

    def exist(self, path: str):
        return path in self.files

    def size(self, path: str) -> int:
        if not self.exist(path):
            raise FileNotFoundError(path)
        return self.files[path].size or 0

    def is_dir(self, path: str):
        if not self.exist(path):
            raise FileNotFoundError(path)
        return self.files[path].is_dir

    def last_modified(self, path: str) -> float:
        if not self.exist(path):
            raise FileNotFoundError(path)
        return time.mktime(self.files[path].last_modified.timetuple())

    def put(self, path: str, fo: IO[bytes], size: int):
        self.cl.put_object(
            bucket_name=self.bucket_name, object_name=path, data=fo, length=size
        )

    @contextmanager
    def open(self, path):
        if not self.exist(path):
            raise FileNotFoundError(path)
        resp = None
        try:
            resp = self.cl.get_object(bucket_name=self.bucket_name, object_name=path)
            yield resp
        finally:
            if resp is not None:
                resp.close()
                resp.release_conn()

    def mkdir(self, path: str):
        # In Minio directories are created
        # automatically when files are created.
        pass

    def close(self) -> None:
        pass


class FtpFS(RemoteFS):

    client: SFTPClient
    files: dict[str, SFTPAttributes]

    @classmethod
    def from_credentials(
        cls,
        uri,
        username,
        password,
        path,
        keyfile_path=None,
        missing_host_key_policy: MissingHostKeyPolicy | None = None,
    ) -> FtpFS:
        # with urlparse(uri, scheme="sftp") the uri
        # is interpreted as relative path
        uri_parts = urlparse(uri if "://" in uri else f"sftp://{uri}")
        if uri_parts.scheme != "sftp":
            # NOTE:
            # We log the wrong scheme but do try to connect anyways...
            # Should we fail instead?
            logger.warning(
                f"Expected URI to start with sftp://... , "
                f"not with {uri_parts.scheme}://... '"
            )
        ssh = SSHClient()
        if missing_host_key_policy is not None:
            ssh.set_missing_host_key_policy(missing_host_key_policy)
        if password:  # either pwd or keyfile
            keyfile_path = None
        ssh.connect(
            hostname=uri_parts.hostname,
            port=uri_parts.port or SSH_PORT,
            username=username,
            password=password or None,
            key_filename=keyfile_path,
            look_for_keys=False,  # todo maybe ?
            allow_agent=False,
            compress=True,
            timeout=10,
        )
        cl = ssh.open_sftp()
        return cls(connection=ssh, client=cl, path=path)

    def __init__(
        self, connection: SSHClient, client: SFTPClient, path: str = "."
    ) -> None:
        self.connection = connection
        self.client = client
        self.path = path
        self.files = {}
        self.client.chdir(self.path)
        self._get_files()

    def _get_files(self, path=""):
        # Note that directories always appear
        # before any files from that directory
        # appear.
        dirs = []
        # we must avoid calling listdir_iter multiple
        # times, otherwise it might cause a deadlock.
        # That's why we do not recurse within the loop.
        for attrs in self.client.listdir_iter(path):
            file_path = os.path.join(path, attrs.filename)
            if stat.S_ISDIR(attrs.st_mode):
                dirs.append(file_path)
            self.files[file_path] = attrs
        for dir_ in dirs:
            self._get_files(dir_)

    def exist(self, path: str):
        return path in self.files

    def size(self, path: str):
        if not self.exist(path):
            raise FileNotFoundError(path)
        return self.files[path].st_size or 0

    def is_dir(self, path: str):
        if not self.exist(path):
            raise FileNotFoundError(path)
        return stat.S_ISDIR(self.files[path].st_mode)

    def put(self, path: str, fo: IO[bytes], size: int):
        self.client.putfo(fl=fo, remotepath=path, file_size=size)

    def mkdir(self, path: str) -> None:
        logger.debug(f"CREATE {path}")
        self.client.mkdir(path)

    def last_modified(self, path: str) -> int:
        if not self.exist(path):
            raise FileNotFoundError(path)
        return self.files[path].st_mtime or 0

    @contextmanager
    def open(self, path):
        if not self.exist(path):
            raise FileNotFoundError(path)
        with self.client.open(path, mode="r") as fo:
            yield fo

    def close(self):
        self.client.close()
        self.connection.close()


def sync(src: RemoteFS, trg: RemoteFS, thing_id: str):
    """Sync two remote filesystems."""

    path = None
    try:
        logging.info(f"{len(src.files)} files found in source directory")
        synced = 0
        for path in src.files:
            logger.debug(f"SYNCING: {path}")

            # dirs
            if src.is_dir(path):
                if not trg.exist(path):
                    trg.mkdir(path)
                continue

            # regular files
            if (
                not trg.exist(path)
                or src.size(path) != trg.size(path)
                or src.last_modified(path) > trg.last_modified(path)
            ):
                trg.update(src, path)
                synced += 1
                continue
    except Exception:
        journal.error(
            f"SFTP sync job failed for path: {path} and for thing {thing_id}", thing_id
        )
        raise
    else:
        journal.info(
            f"SFTP sync job ran successfully. {synced} files synced for "
            f"thing {thing_id}",
            thing_id,
        )
