"""Private storage abstraction for local development and S3-compatible production storage."""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator

from app.core.config import settings


class StorageService:
    def __init__(self) -> None:
        self._s3 = None
        if settings.storage_backend == "s3":
            try:
                import boto3
            except ImportError as exc:  # pragma: no cover - exercised in storage image/CI
                raise RuntimeError("Install backend/requirements-storage.txt for S3 storage") from exc
            self._s3 = boto3.client("s3", endpoint_url=settings.storage_endpoint_url or None)

    def _key(self, key: str) -> str:
        return f"{settings.storage_prefix.rstrip('/')}/{key.lstrip('/')}"

    def put_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        if self._s3 is not None:
            self._s3.put_object(Bucket=settings.storage_bucket, Key=self._key(key), Body=data, ContentType=content_type)
            return
        path = self._local_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read_bytes(self, key: str) -> bytes:
        if self._s3 is not None:
            return self._s3.get_object(Bucket=settings.storage_bucket, Key=self._key(key))["Body"].read()
        return self._local_path(key).read_bytes()

    def delete(self, key: str | None) -> None:
        if not key:
            return
        if self._s3 is not None:
            self._s3.delete_object(Bucket=settings.storage_bucket, Key=self._key(key))
            return
        path = self._local_path(key)
        if path.is_file():
            path.unlink()

    @contextmanager
    def materialize(self, key: str) -> Iterator[Path]:
        if self._s3 is None:
            path = self._local_path(key)
            yield path
            return
        with tempfile.NamedTemporaryFile(suffix=Path(key).suffix, delete=False) as handle:
            temporary = Path(handle.name)
        try:
            temporary.write_bytes(self.read_bytes(key))
            yield temporary
        finally:
            temporary.unlink(missing_ok=True)

    def _local_path(self, key: str) -> Path:
        root = Path(settings.upload_dir).resolve()
        processed_root = Path(settings.processed_dir).resolve()
        relative = Path(key)
        base = processed_root if key.startswith("processed/") else root
        path = (base / relative.name).resolve()
        if base not in path.parents:
            raise ValueError("Invalid private storage key")
        return path


storage = StorageService()
