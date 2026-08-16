from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import asdict
from datetime import date
from pathlib import Path

import pytest

from castforge.config import load_config
from castforge.models import EpisodeManifest
from castforge.runner import NoEpisodeResult, run_episode


def test_no_episode_result_preserves_ledger_path_compatibility() -> None:
    result = NoEpisodeResult(ledger_path=Path("legacy-ledger.json"))

    assert result.ledger_path == Path("legacy-ledger.json")
    assert asdict(result)["ledger_path"] == Path("legacy-ledger.json")


def test_fixture_run_is_source_qualified_and_idempotent(show_project) -> None:
    config = load_config(show_project())
    first = run_episode(config, date(2026, 8, 11))
    second = run_episode(config, date(2026, 8, 11))

    assert first == second
    assert first.created_at == "2026-08-11T13:00:00Z"
    assert {story.id for story in first.stories} == {"acme-releases-a-model", "builder-tool-adds-local-inference"}
    root = ET.parse(config.outputs.feed).getroot()
    assert len(root.findall("./channel/item")) == 1
    assert root.findtext("./channel/item/guid") == "test-show-2026-08-11"
    assert EpisodeManifest.read(config.outputs.manifests / "2026-08-11.json") == first


def test_shadow_run_does_not_create_feed(show_project) -> None:
    config = load_config(show_project())
    run_episode(config, date(2026, 8, 11), shadow=True)
    assert not config.outputs.feed.exists()
    assert (config.outputs.manifests / "2026-08-11.json").is_file()


def test_audio_failure_leaves_existing_feed_unchanged(show_project, monkeypatch) -> None:
    config = load_config(show_project(audio_provider="notebooklm", fixture_length=0))
    config.outputs.feed.parent.mkdir(parents=True, exist_ok=True)
    config.outputs.feed.write_text("existing-feed", encoding="utf-8")

    def fail_audio(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("castforge.runner.publish_audio", fail_audio)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        run_episode(config, date(2026, 8, 11))
    assert config.outputs.feed.read_text(encoding="utf-8") == "existing-feed"
