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
