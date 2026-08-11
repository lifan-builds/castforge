"""Configuration loading for generic CastForge show repositories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml


def _mapping(raw: Any, name: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{name} must be a mapping")
    return raw


def _text(raw: dict[str, Any], key: str, section: str) -> str:
    value = str(raw.get(key, "") or "").strip()
    if not value:
        raise ValueError(f"{section}.{key} is required")
    return value


@dataclass(frozen=True, slots=True)
class ShowConfig:
    slug: str
    title: str
    description: str
    language: str
    author: str
    site_url: str
    feed_url: str
    cover_art_url: str
    episode_guid_prefix: str
    episode_file_prefix: str
    cadence: str
    timezone: str
    publication_hour: int


@dataclass(frozen=True, slots=True)
class SourceConfig:
    fixture: Path


@dataclass(frozen=True, slots=True)
class SelectionConfig:
    max_stories: int = 5
    max_per_organization: int = 1
    max_per_category: int = 1
    recent_days: int = 7


@dataclass(frozen=True, slots=True)
class AudioConfig:
    provider: str
    output_dir: Path
    duration: str
    public_url_template: str
    fixture_length_bytes: int = 0
    language: str = "en"
    instructions: str = ""
    audio_length: str = "short"


@dataclass(frozen=True, slots=True)
class PublicationConfig:
    provider: str
    bucket: str = ""
    endpoint_url: str = ""
    public_base_url: str = ""
    access_key_env: str = "R2_ACCESS_KEY_ID"
    secret_key_env: str = "R2_SECRET_ACCESS_KEY"
    download_url_prefix: str = ""


@dataclass(frozen=True, slots=True)
class OutputConfig:
    root: Path
    feed: Path
    manifests: Path
    sources: Path


@dataclass(frozen=True, slots=True)
class PodcastConfig:
    path: Path
    show: ShowConfig
    source: SourceConfig
    selection: SelectionConfig
    audio: AudioConfig
    publication: PublicationConfig
    outputs: OutputConfig


def _resolve(base: Path, value: Any, default: str) -> Path:
    candidate = Path(str(value or default))
    return candidate if candidate.is_absolute() else (base / candidate).resolve()


def load_config(path: Path) -> PodcastConfig:
    config_path = Path(path).resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    root = _mapping(raw, "config")
    if int(root.get("version", 0)) != 1:
        raise ValueError("version must be 1")

    base = config_path.parent
    show_raw = _mapping(root.get("show"), "show")
    timezone = _text(show_raw, "timezone", "show")
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as error:
        raise ValueError(f"unknown timezone: {timezone}") from error
    cadence = str(show_raw.get("cadence", "daily")).strip()
    if cadence not in {"daily", "weekly"}:
        raise ValueError("show.cadence must be daily or weekly")
    show = ShowConfig(
        slug=_text(show_raw, "slug", "show"),
        title=_text(show_raw, "title", "show"),
        description=_text(show_raw, "description", "show"),
        language=_text(show_raw, "language", "show"),
        author=_text(show_raw, "author", "show"),
        site_url=_text(show_raw, "site_url", "show"),
        feed_url=_text(show_raw, "feed_url", "show"),
        cover_art_url=_text(show_raw, "cover_art_url", "show"),
        episode_guid_prefix=_text(show_raw, "episode_guid_prefix", "show"),
        episode_file_prefix=_text(show_raw, "episode_file_prefix", "show"),
        cadence=cadence,
        timezone=timezone,
        publication_hour=int(show_raw.get("publication_hour", 6)),
    )
    if show.publication_hour < 0 or show.publication_hour > 23:
        raise ValueError("show.publication_hour must be between 0 and 23")

    source_raw = _mapping(root.get("source"), "source")
    source = SourceConfig(fixture=_resolve(base, source_raw.get("fixture"), "fixtures/sources.json"))

    selection_raw = _mapping(root.get("selection", {}), "selection")
    selection = SelectionConfig(
        max_stories=int(selection_raw.get("max_stories", 5)),
        max_per_organization=int(selection_raw.get("max_per_organization", 1)),
        max_per_category=int(selection_raw.get("max_per_category", 1)),
        recent_days=int(selection_raw.get("recent_days", 7)),
    )
    if min(
        selection.max_stories,
        selection.max_per_organization,
        selection.max_per_category,
    ) < 1:
        raise ValueError("selection limits must be positive")

    audio_raw = _mapping(root.get("audio"), "audio")
    audio = AudioConfig(
        provider=_text(audio_raw, "provider", "audio"),
        output_dir=_resolve(base, audio_raw.get("output_dir"), "build/audio"),
        duration=str(audio_raw.get("duration", "00:06:00")),
        public_url_template=_text(audio_raw, "public_url_template", "audio"),
        fixture_length_bytes=int(audio_raw.get("fixture_length_bytes", 0)),
        language=str(audio_raw.get("language", show.language)),
        instructions=str(audio_raw.get("instructions", "") or ""),
        audio_length=str(audio_raw.get("audio_length", "short") or "short"),
    )
    if audio.provider not in {"fixture", "notebooklm"}:
        raise ValueError("audio.provider must be fixture or notebooklm")
    if audio.provider == "fixture" and audio.fixture_length_bytes < 1:
        raise ValueError("audio.fixture_length_bytes must be positive for fixture audio")

    publication_raw = _mapping(root.get("publication", {"provider": "fixture"}), "publication")
    publication = PublicationConfig(
        provider=str(publication_raw.get("provider", "fixture") or "fixture"),
        bucket=str(publication_raw.get("bucket", "") or ""),
        endpoint_url=str(publication_raw.get("endpoint_url", "") or ""),
        public_base_url=str(publication_raw.get("public_base_url", "") or ""),
        access_key_env=str(publication_raw.get("access_key_env", "R2_ACCESS_KEY_ID")),
        secret_key_env=str(publication_raw.get("secret_key_env", "R2_SECRET_ACCESS_KEY")),
        download_url_prefix=str(publication_raw.get("download_url_prefix", "") or ""),
    )
    if publication.provider not in {"fixture", "r2"}:
        raise ValueError("publication.provider must be fixture or r2")
    if publication.provider == "r2" and not all(
        (publication.bucket, publication.endpoint_url, publication.public_base_url)
    ):
        raise ValueError("R2 publication requires bucket, endpoint_url, and public_base_url")
    if publication.provider == "r2" and audio.provider == "fixture":
        raise ValueError("R2 publication requires non-fixture audio")

    output_raw = _mapping(root.get("outputs", {}), "outputs")
    output_root = _resolve(base, output_raw.get("root"), "build")
    outputs = OutputConfig(
        root=output_root,
        feed=_resolve(base, output_raw.get("feed"), "build/feed.xml"),
        manifests=_resolve(base, output_raw.get("manifests"), "build/manifests"),
        sources=_resolve(base, output_raw.get("sources"), "build/sources"),
    )
    return PodcastConfig(
        path=config_path,
        show=show,
        source=source,
        selection=selection,
        audio=audio,
        publication=publication,
        outputs=outputs,
    )
