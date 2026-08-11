from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def show_project(tmp_path: Path):
    def create(*, audio_provider: str = "fixture", fixture_length: int = 1024) -> Path:
        config = tmp_path / "podcast.yaml"
        fixture = tmp_path / "fixtures" / "sources.json"
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text(
            json.dumps(
                {
                    "items": [
                        {
                            "id": "release-primary",
                            "title": "Acme releases a model",
                            "url": "https://acme.example/releases/model",
                            "source": "Acme",
                            "published_at": "2026-08-11T12:00:00Z",
                            "summary": "Acme released a documented model update.",
                            "authority": "primary",
                            "organization": "Acme",
                            "category": "models",
                            "metadata": {"score": 100, "selection_reason": "Primary model release"},
                        },
                        {
                            "id": "tool-primary",
                            "title": "Builder tool adds local inference",
                            "url": "https://tools.example/releases/local",
                            "source": "Builder Tools",
                            "published_at": "2026-08-11T11:00:00Z",
                            "summary": "The tool added a documented local inference path.",
                            "authority": "primary",
                            "organization": "Builder Tools",
                            "category": "developer tools",
                            "metadata": {"score": 90, "selection_reason": "Direct builder impact"},
                        },
                        {
                            "id": "rumor-signal",
                            "title": "Unverified model rumor",
                            "url": "https://social.example/rumor",
                            "source": "Social Signal",
                            "published_at": "2026-08-11T10:00:00Z",
                            "summary": "An unverified account claimed a model was imminent.",
                            "authority": "signal",
                            "organization": "Rumor Mill",
                            "category": "models",
                            "metadata": {"score": 1000},
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        config.write_text(
            f"""version: 1
show:
  slug: test-show
  title: Test Show
  description: Test description
  language: en
  author: Test Author
  site_url: https://example.com/
  feed_url: https://example.com/feed.xml
  cover_art_url: https://example.com/cover.png
  episode_guid_prefix: test-show
  episode_file_prefix: test-show
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
  provider: {audio_provider}
  output_dir: build/audio
  duration: 00:06:00
  public_url_template: https://audio.example/episodes/{{filename}}
  fixture_length_bytes: {fixture_length}
  language: en
  audio_length: short
publication:
  provider: fixture
outputs:
  root: build
  feed: build/feed.xml
  manifests: build/manifests
  sources: build/sources
""",
            encoding="utf-8",
        )
        return config

    return create
