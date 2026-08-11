"""Cloudflare R2 publication through its S3-compatible API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen


def validate_public_audio(
    url: str,
    *,
    expected_length: int | None = None,
    opener: Callable[..., Any] = urlopen,
    timeout: float = 60,
) -> None:
    request = Request(url, method="HEAD", headers={"User-Agent": "CastForge/0.1"})
    with opener(request, timeout=timeout) as response:
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
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.client = client
        self.bucket = bucket
        self.public_base_url = public_base_url.rstrip("/")
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
        return cls(client=client, bucket=bucket, public_base_url=public_base_url)

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
