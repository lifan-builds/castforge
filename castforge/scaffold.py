"""Minimal show scaffold used by ``castforge init``."""

from __future__ import annotations

import json
from pathlib import Path

PODCAST_YAML = """version: 1

show:
  slug: example-podcast
  title: Example Podcast
  description: A source-transparent podcast powered by CastForge.
  language: en
  author: Example Publisher
  site_url: https://example.com/podcast/
  feed_url: https://example.com/podcast/feed.xml
  cover_art_url: https://example.com/podcast/cover.png
  episode_guid_prefix: example-podcast
  episode_file_prefix: example-podcast
  cadence: daily
  timezone: America/Los_Angeles
  publication_hour: 6

source:
  fixture: fixtures/sources.json

selection:
  max_stories: 5
  max_per_organization: 1
  max_per_category: 1
  recent_days: 7

audio:
  provider: fixture
  output_dir: build/audio
  duration: 00:06:00
  public_url_template: https://example.com/podcast/episodes/{filename}
  fixture_length_bytes: 1024
  language: en
  audio_length: short

publication:
  provider: fixture

outputs:
  root: build
  feed: build/feed.xml
  manifests: build/manifests
  sources: build/sources
"""

FIXTURE = {
    "items": [
        {
            "id": "example-primary",
            "title": "Example project publishes a new release",
            "url": "https://example.com/releases/1",
            "source": "Example Project",
            "published_at": "2026-08-11T12:00:00Z",
            "summary": "The project published a documented release for developers.",
            "authority": "primary",
            "organization": "Example Project",
            "category": "developer tools",
            "metadata": {"score": 100, "selection_reason": "Primary release with builder impact"},
        },
        {
            "id": "example-research",
            "title": "Example research result improves inference",
            "url": "https://example.org/papers/1",
            "source": "Example Research Lab",
            "published_at": "2026-08-11T11:00:00Z",
            "summary": "A cited paper reports a reproducible inference improvement.",
            "authority": "primary",
            "organization": "Example Research Lab",
            "category": "research",
            "metadata": {"score": 90, "selection_reason": "Primary research with reproducible evidence"},
        },
    ]
}


def initialize_show(directory: Path) -> list[Path]:
    destination = Path(directory).resolve()
    config_path = destination / "podcast.yaml"
    fixture_path = destination / "fixtures" / "sources.json"
    conflicts = [path for path in (config_path, fixture_path) if path.exists()]
    if conflicts:
        raise FileExistsError(f"refusing to overwrite existing file: {conflicts[0]}")
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(PODCAST_YAML, encoding="utf-8")
    fixture_path.write_text(json.dumps(FIXTURE, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return [config_path, fixture_path]
