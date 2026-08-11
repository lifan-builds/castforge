from __future__ import annotations

from email.message import Message

import pytest

from castforge.publishers.r2 import R2Publisher


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def put_object(self, **kwargs) -> None:
        body = kwargs.pop("Body")
        self.calls.append({**kwargs, "body": body.read()})


class CapacityClient(FakeClient):
    def __init__(self, pages) -> None:
        super().__init__()
        self.pages = pages
        self.list_calls = []

    def list_objects_v2(self, **kwargs):
        self.list_calls.append(kwargs)
        return self.pages[len(self.list_calls) - 1]


class FakeResponse:
    def __init__(self, *, content_type: str, content_length: int) -> None:
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.headers["Content-Length"] = str(content_length)

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None

    def getcode(self) -> int:
        return self.status


def test_r2_upload_sets_mime_and_validates_public_object(tmp_path) -> None:
    audio = tmp_path / "episode.mp3"
    audio.write_bytes(b"mp3-data")
    client = FakeClient()

    def open_public(request, *, timeout):
        assert request.full_url == "https://audio.example/episodes/episode.mp3"
        return FakeResponse(content_type="audio/mpeg", content_length=8)

    publisher = R2Publisher(
        client=client,
        bucket="episodes",
        public_base_url="https://audio.example",
        opener=open_public,
    )
    assert publisher.publish(audio, "episodes/episode.mp3") == "https://audio.example/episodes/episode.mp3"
    assert client.calls[0]["ContentType"] == "audio/mpeg"
    assert client.calls[0]["body"] == b"mp3-data"


def test_r2_rejects_wrong_public_mime(tmp_path) -> None:
    audio = tmp_path / "episode.mp3"
    audio.write_bytes(b"mp3-data")
    publisher = R2Publisher(
        client=FakeClient(),
        bucket="episodes",
        public_base_url="https://audio.example",
        opener=lambda request, timeout: FakeResponse(
            content_type="application/octet-stream",
            content_length=8,
        ),
    )
    with pytest.raises(RuntimeError, match="wrong content type"):
        publisher.publish(audio, "episodes/episode.mp3")


def test_r2_rejects_upload_above_bucket_limit(tmp_path) -> None:
    audio = tmp_path / "episode.mp3"
    audio.write_bytes(b"mp3-data")
    client = CapacityClient(
        [{"Contents": [{"Key": "episodes/old.mp3", "Size": 8_999_999_995}]}]
    )
    publisher = R2Publisher(
        client=client,
        bucket="episodes",
        public_base_url="https://audio.example",
        max_bucket_bytes=9_000_000_000,
    )

    with pytest.raises(RuntimeError, match="bucket limit would be exceeded"):
        publisher.publish(audio, "episodes/episode.mp3")
    assert client.calls == []


def test_r2_bucket_limit_accounts_for_paginated_overwrite(tmp_path) -> None:
    audio = tmp_path / "episode.mp3"
    audio.write_bytes(b"mp3-data")
    client = CapacityClient(
        [
            {
                "Contents": [{"Key": "episodes/old.mp3", "Size": 8_899_999_992}],
                "IsTruncated": True,
                "NextContinuationToken": "next-page",
            },
            {
                "Contents": [{"Key": "episodes/episode.mp3", "Size": 100_000_000}],
                "IsTruncated": False,
            },
        ]
    )
    publisher = R2Publisher(
        client=client,
        bucket="episodes",
        public_base_url="https://audio.example",
        max_bucket_bytes=9_000_000_000,
        opener=lambda request, timeout: FakeResponse(
            content_type="audio/mpeg",
            content_length=8,
        ),
    )

    publisher.publish(audio, "episodes/episode.mp3")
    assert client.list_calls[1]["ContinuationToken"] == "next-page"
    assert len(client.calls) == 1
