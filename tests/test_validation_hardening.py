# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lifan-builds. CastForge; Section 7 attribution terms in ATTRIBUTION.md.
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from castforge.config import load_config
from castforge.runner import run_episode
from castforge.validation import validate_project


@pytest.fixture
def episode(show_project):
    config = load_config(show_project())
    manifest = run_episode(config, date(2024, 2, 29))
    return config, manifest


@pytest.mark.parametrize("episode_date", ["", "2025-02-29", "20240229", "../2024-02-29"])
def test_invalid_date_precedes_manifest_access(show_project, episode_date):
    config = load_config(show_project())
    with patch.object(Path, "glob") as glob, patch("castforge.validation.EpisodeManifest.read") as read:
        assert validate_project(config, episode_date=episode_date) == ["episode_date must be a valid YYYY-MM-DD date"]
        glob.assert_not_called()
        read.assert_not_called()


def test_date_selects_one_manifest_and_none_selects_all(episode):
    config, _ = episode
    other = config.outputs.manifests / "2024-03-01.json"
    other.write_text("{", encoding="utf-8")
    assert validate_project(config, episode_date="2024-02-29") == []
    error, = validate_project(config, episode_date=None)
    assert str(other) in error


@pytest.mark.parametrize("url", [None, "", "  "])
@pytest.mark.parametrize("check_public", [False, True])
def test_enclosure_requires_nonblank_url(episode, url, check_public):
    config, manifest = episode
    feed = ET.parse(config.outputs.feed)
    enclosure = feed.find("./channel/item/enclosure")
    if url is None:
        del enclosure.attrib["url"]
    else:
        enclosure.set("url", url)
    feed.write(config.outputs.feed)
    with patch("castforge.validation.validate_public_audio") as probe:
        assert validate_project(config, check_public=check_public) == [f"missing enclosure URL for {manifest.episode_id}"]
        probe.assert_not_called()


@pytest.mark.parametrize("failure", ["invalid UTF-8", "permission denied"])
def test_unreadable_source_and_feed_error_are_both_reported(episode, monkeypatch, failure):
    config, manifest = episode
    source = config.path.parent / manifest.source_document
    if failure == "invalid UTF-8":
        source.write_bytes(b"\xff")
    else:
        read_text = Path.read_text

        def read_with_denied_source(path, *args, **kwargs):
            if path == source:
                raise PermissionError("permission denied")
            return read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read_with_denied_source)
    feed = ET.parse(config.outputs.feed)
    feed.find("./channel/item/enclosure").set("length", "0")
    feed.write(config.outputs.feed)
    source_error, enclosure_error = validate_project(config)
    assert f"unreadable source document for {manifest.episode_id}: {source}" in source_error
    assert enclosure_error == f"non-positive enclosure length for {manifest.episode_id}"


@pytest.mark.parametrize(
    "version",
    ["", "version: null", "version: true", "version: 1.0", "version: 1.9", "version: latest", "version: 3"],
)
def test_invalid_version_has_field_specific_error(show_project, version):
    path = show_project()
    path.write_text(path.read_text().replace("version: 1", version))
    with pytest.raises(ValueError, match="^version must be 1 or 2$"):
        load_config(path)


@pytest.mark.parametrize("version", ["1", "2", "'1'", "'2'"])
def test_supported_versions(show_project, version):
    path = show_project()
    path.write_text(path.read_text().replace("version: 1", f"version: {version}"))
    assert load_config(path).path == path


@pytest.mark.parametrize("limit", [".nan", ".inf", "-.inf", "0", "-1"])
def test_duration_limit_must_be_positive_and_finite(show_project, limit):
    path = show_project()
    path.write_text(path.read_text().replace("audio:\n", f"audio:\n  max_duration_seconds: {limit}\n"))
    with pytest.raises(ValueError, match=r"audio\.max_duration_seconds must be positive and finite"):
        load_config(path)
