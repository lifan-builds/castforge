from __future__ import annotations

from pathlib import Path

import pytest

from castforge import notebooklm_audio


class FakeResult:
    id = "source-1"
    is_error = False


class FakeFinal:
    is_failed = False
    is_complete = True
    status = "complete"
    error = None
    task_id = "audio-1"


class FakeSources:
    def __init__(self, calls) -> None:
        self.calls = calls

    async def add_file(self, notebook_id, path, *, wait, wait_timeout):
        self.calls.append("add")
        return FakeResult()

    async def delete(self, notebook_id, source_id):
        self.calls.append("delete")


class FakeArtifacts:
    def __init__(self, calls, *, fail=False) -> None:
        self.calls = calls
        self.fail = fail

    async def generate_audio(self, *args, **kwargs):
        self.calls.append(("generate", kwargs.get("audio_length")))
        return type("Status", (), {"task_id": "task-1"})()

    async def wait_for_completion(self, *args, **kwargs):
        self.calls.append("wait")
        if self.fail:
            raise RuntimeError("generation failed")
        return FakeFinal()

    async def download_audio(self, notebook_id, output, *, artifact_id):
        self.calls.append("download")
        Path(output).write_bytes(b"audio")


class FakeClient:
    def __init__(self, calls, *, fail=False) -> None:
        self.sources = FakeSources(calls)
        self.artifacts = FakeArtifacts(calls, fail=fail)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


def fake_sdk(calls, *, fail=False):
    class ClientFactory:
        @staticmethod
        async def from_storage(*args, **kwargs):
            return FakeClient(calls, fail=fail)

    class AudioFormat:
        DEEP_DIVE = "deep"
        BRIEF = "brief"
        CRITIQUE = "critique"
        DEBATE = "debate"

    class AudioLength:
        SHORT = "short"
        DEFAULT = "default"
        LONG = "long"

    return ClientFactory, AudioFormat, AudioLength


def test_temporary_source_deleted_after_success(tmp_path, monkeypatch) -> None:
    calls = []
    source = tmp_path / "source.md"
    source.write_text("source", encoding="utf-8")
    monkeypatch.setenv("NOTEBOOKLM_NOTEBOOK_ID", "notebook")
    monkeypatch.setattr(notebooklm_audio, "_ensure_notebooklm_imported", lambda: fake_sdk(calls))
    output = notebooklm_audio.publish_audio(source, tmp_path / "episode.mp3")
    assert output.read_bytes() == b"audio"
    assert calls[-1] == "delete"


def test_temporary_source_deleted_after_generation_failure(tmp_path, monkeypatch) -> None:
    calls = []
    source = tmp_path / "source.md"
    source.write_text("source", encoding="utf-8")
    monkeypatch.setenv("NOTEBOOKLM_NOTEBOOK_ID", "notebook")
    monkeypatch.setattr(
        notebooklm_audio,
        "_ensure_notebooklm_imported",
        lambda: fake_sdk(calls, fail=True),
    )
    with pytest.raises(RuntimeError, match="generation failed"):
        notebooklm_audio.publish_audio(source, tmp_path / "episode.mp3")
    assert calls[-1] == "delete"


def test_overlong_audio_retries_once_at_short_length(tmp_path, monkeypatch) -> None:
    calls = []
    durations = iter((901.0, 600.0))
    source = tmp_path / "source.md"
    source.write_text("source", encoding="utf-8")
    monkeypatch.setenv("NOTEBOOKLM_NOTEBOOK_ID", "notebook")
    monkeypatch.setattr(notebooklm_audio, "_ensure_notebooklm_imported", lambda: fake_sdk(calls))
    monkeypatch.setattr(notebooklm_audio, "probe_audio_duration", lambda path: next(durations))
    notebooklm_audio.publish_audio(
        source,
        tmp_path / "episode.mp3",
        audio_length_name="default",
        max_duration_seconds=900,
    )
    assert [call for call in calls if isinstance(call, tuple)] == [
        ("generate", "default"),
        ("generate", "short"),
    ]


def test_audio_still_over_ceiling_after_short_retry_fails_closed(tmp_path, monkeypatch) -> None:
    calls = []
    durations = iter((901.0, 901.0))
    source = tmp_path / "source.md"
    source.write_text("source", encoding="utf-8")
    monkeypatch.setenv("NOTEBOOKLM_NOTEBOOK_ID", "notebook")
    monkeypatch.setattr(notebooklm_audio, "_ensure_notebooklm_imported", lambda: fake_sdk(calls))
    monkeypatch.setattr(notebooklm_audio, "probe_audio_duration", lambda path: next(durations))
    with pytest.raises(RuntimeError, match="exceeds maximum duration"):
        notebooklm_audio.publish_audio(
            source,
            tmp_path / "episode.mp3",
            audio_length_name="default",
            max_duration_seconds=900,
        )
    assert calls[-1] == "delete"
