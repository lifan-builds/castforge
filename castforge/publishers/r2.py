"""Cloudflare R2 publication through its S3-compatible API."""

from __future__ import annotations

import os
import ssl
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

import certifi


def validate_public_audio(
    url: str,
    *,
    expected_length: int | None = None,
    opener: Callable[..., Any] | None = None,
    timeout: float = 60,
) -> None:
    request = Request(url, method="HEAD", headers={"User-Agent": "CastForge/0.1"})
    effective_opener = opener or urlopen
    kwargs: dict[str, Any] = {"timeout": timeout}
    if opener is None:
        kwargs["context"] = ssl.create_default_context(cafile=certifi.where())
    with effective_opener(request, **kwargs) as response:
        status = getattr(response, "status", response.getcode())
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
        content_length = int(response.headers.get("Content-Length", "0") or 0)
    if status != 200:
        raise RuntimeError(f"public audio returned HTTP {status}: {url}")
    if content_type != "audio/mpeg":
        raise RuntimeError(f"public audio has wrong content type {content_type!r}: {url}")
    if content_length < 1:
        raise RuntimeError(f"public audio has no content length: {url}")
    if expected_length is not None and content_length != expected_length:
        raise RuntimeError(
            f"public audio length mismatch: expected {expected_length}, got {content_length}"
        )


class R2Publisher:
    def __init__(
        self,
        *,
        client: Any,
        bucket: str,
        public_base_url: str,
        max_bucket_bytes: int = 0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.client = client
        self.bucket = bucket
        self.public_base_url = public_base_url.rstrip("/")
        self.max_bucket_bytes = max_bucket_bytes
        self.opener = opener

    @classmethod
    def from_env(
        cls,
        *,
        bucket: str,
        endpoint_url: str,
        public_base_url: str,
        access_key_env: str = "R2_ACCESS_KEY_ID",
        secret_key_env: str = "R2_SECRET_ACCESS_KEY",
        max_bucket_bytes: int = 0,
    ) -> "R2Publisher":
        access_key = os.environ.get(access_key_env, "").strip()
        secret_key = os.environ.get(secret_key_env, "").strip()
        if not access_key or not secret_key:
            raise RuntimeError(f"R2 credentials are required in {access_key_env} and {secret_key_env}")
        try:
            import boto3
        except ImportError as error:
            raise RuntimeError('Install the R2 integration with: pip install "castforge[r2]"') from error
        client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
        )
        return cls(
            client=client,
            bucket=bucket,
            public_base_url=public_base_url,
            max_bucket_bytes=max_bucket_bytes,
        )

    def _bucket_usage(self, object_key: str) -> tuple[int, int]:
        total = 0
        replaced_size = 0
        continuation_token: str | None = None
        while True:
            request = {"Bucket": self.bucket}
            if continuation_token:
                request["ContinuationToken"] = continuation_token
            page = self.client.list_objects_v2(**request)
            for item in page.get("Contents", []):
                size = int(item.get("Size", 0))
                total += size
                if item.get("Key") == object_key:
                    replaced_size = size
            if not page.get("IsTruncated"):
                return total, replaced_size
            continuation_token = page.get("NextContinuationToken")
            if not continuation_token:
                raise RuntimeError("R2 bucket listing was truncated without a continuation token")

    def publish(self, local_audio: Path, object_key: str) -> str:
        audio = Path(local_audio)
        if not audio.is_file():
            raise FileNotFoundError(f"audio file not found: {audio}")
        size = audio.stat().st_size
        if size < 1:
            raise ValueError("audio file is empty")
        if audio.suffix.lower() != ".mp3":
            raise ValueError("R2 publisher currently accepts MP3 audio only")
        normalized_key = object_key.lstrip("/")
        if self.max_bucket_bytes:
            bucket_size, replaced_size = self._bucket_usage(normalized_key)
            projected_size = bucket_size - replaced_size + size
            if projected_size > self.max_bucket_bytes:
                raise RuntimeError(
                    "R2 bucket limit would be exceeded: "
                    f"projected {projected_size} bytes > {self.max_bucket_bytes} bytes"
                )
        with audio.open("rb") as handle:
            self.client.put_object(
                Bucket=self.bucket,
                Key=normalized_key,
                Body=handle,
                ContentType="audio/mpeg",
                CacheControl="public, max-age=31536000, immutable",
            )
        public_url = f"{self.public_base_url}/{normalized_key}"
        validate_public_audio(
            public_url,
            expected_length=size,
            opener=self.opener,
        )
        return public_url
