"""Serializable contracts shared by CastForge shows and pipeline stages."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

SourceAuthority = Literal["primary", "independent", "signal"]


def _required_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


@dataclass(frozen=True, slots=True)
class SourceItem:
    """One normalized source discovered by a show-owned adapter."""

    id: str
    title: str
    url: str
    source: str
    published_at: str
    summary: str
    authority: SourceAuthority = "signal"
    organization: str = ""
    category: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("id", "title", "url", "source", "published_at", "summary"):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))
        if self.authority not in {"primary", "independent", "signal"}:
            raise ValueError("authority must be primary, independent, or signal")
        try:
            datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("published_at must be ISO 8601") from error

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SourceItem":
        return cls(
            id=raw.get("id", ""),
            title=raw.get("title", ""),
            url=raw.get("url", ""),
            source=raw.get("source", ""),
            published_at=raw.get("published_at", ""),
            summary=raw.get("summary", ""),
            authority=raw.get("authority", "signal"),
            organization=str(raw.get("organization", "") or ""),
            category=str(raw.get("category", "") or ""),
            metadata=dict(raw.get("metadata") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StoryCluster:
    """Deduplicated, qualified sources describing one episode story."""

    id: str
    title: str
    summary: str
    category: str
    organization: str
    sources: tuple[SourceItem, ...]
    selection_reason: str

    def __post_init__(self) -> None:
        for name in ("id", "title", "summary", "selection_reason"):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))
        if not self.sources:
            raise ValueError("sources must not be empty")

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "StoryCluster":
        return cls(
            id=raw.get("id", ""),
            title=raw.get("title", ""),
            summary=raw.get("summary", ""),
            category=str(raw.get("category", "") or ""),
            organization=str(raw.get("organization", "") or ""),
            sources=tuple(SourceItem.from_dict(item) for item in raw.get("sources", [])),
            selection_reason=raw.get("selection_reason", ""),
        )

    def is_qualified(self) -> bool:
        if any(item.authority == "primary" for item in self.sources):
            return True
        independent = {item.source.casefold() for item in self.sources if item.authority == "independent"}
        return len(independent) >= 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "category": self.category,
            "organization": self.organization,
            "sources": [item.to_dict() for item in self.sources],
            "selection_reason": self.selection_reason,
        }


@dataclass(frozen=True, slots=True)
class EpisodeManifest:
    """Auditable record of one generated episode."""

    show_slug: str
    episode_id: str
    episode_date: str
    title: str
    created_at: str
    stories: tuple[StoryCluster, ...]
    source_document: str
    pipeline_version: str
    audio_url: str = ""
    duration: str = ""
    transcript_url: str = ""
    chapters_url: str = ""
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name in (
            "show_slug",
            "episode_id",
            "episode_date",
            "title",
            "created_at",
            "source_document",
            "pipeline_version",
        ):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))
        date.fromisoformat(self.episode_date)
        datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        if not self.stories:
            raise ValueError("stories must not be empty")
        if any(not story.is_qualified() for story in self.stories):
            raise ValueError("every story must have a primary source or two independent sources")

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "EpisodeManifest":
        return cls(
            show_slug=raw.get("show_slug", ""),
            episode_id=raw.get("episode_id", ""),
            episode_date=raw.get("episode_date", ""),
            title=raw.get("title", ""),
            created_at=raw.get("created_at", ""),
            stories=tuple(StoryCluster.from_dict(story) for story in raw.get("stories", [])),
            source_document=raw.get("source_document", ""),
            pipeline_version=raw.get("pipeline_version", ""),
            audio_url=str(raw.get("audio_url", "") or ""),
            duration=str(raw.get("duration", "") or ""),
            transcript_url=str(raw.get("transcript_url", "") or ""),
            chapters_url=str(raw.get("chapters_url", "") or ""),
            schema_version=int(raw.get("schema_version", 1)),
        )

    @classmethod
    def read(cls, path: Path) -> "EpisodeManifest":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "show_slug": self.show_slug,
            "episode_id": self.episode_id,
            "episode_date": self.episode_date,
            "title": self.title,
            "created_at": self.created_at,
            "pipeline_version": self.pipeline_version,
            "source_document": self.source_document,
            "audio_url": self.audio_url,
            "duration": self.duration,
            "transcript_url": self.transcript_url,
            "chapters_url": self.chapters_url,
            "stories": [story.to_dict() for story in self.stories],
        }

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path
