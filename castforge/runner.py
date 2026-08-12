"""Config-driven, date-keyed CastForge artifact orchestration."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from castforge import __version__
from castforge.audio import format_duration, probe_audio_duration
from castforge.config import PodcastConfig
from castforge.models import EpisodeManifest, SourceItem, StoryCluster
from castforge.notebooklm_audio import publish_audio
from castforge.publishers.r2 import R2Publisher
from castforge.rss import write_episode


@dataclass(frozen=True, slots=True)
class NoEpisodeResult:
    """Result returned when editorial minimum-story gating is not met."""

    status: str = "no-episode"
    episode_date: date = date.min
    reason: str = ""
    ledger_path: Path | None = None


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _load_fixture(path: Path) -> list[SourceItem]:
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("items") if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        raise ValueError("source fixture must be a list or an object with an items list")
    return [SourceItem.from_dict(item) for item in records]


def _cluster_items(items: list[SourceItem]) -> list[StoryCluster]:
    grouped: dict[str, list[SourceItem]] = defaultdict(list)
    for item in items:
        key = str(item.metadata.get("cluster_id") or item.metadata.get("canonical_url") or _slug(item.title))
        grouped[key].append(item)

    clusters: list[StoryCluster] = []
    for key, sources in grouped.items():
        ordered = sorted(
            sources,
            key=lambda item: ({"primary": 0, "independent": 1, "analysis": 2, "signal": 3}[item.authority], item.id),
        )
        lead = ordered[0]
        cluster = StoryCluster(
            id=_slug(key) or lead.id,
            title=lead.title,
            summary=lead.summary,
            category=lead.category,
            organization=lead.organization,
            sources=tuple(ordered),
            selection_reason=str(lead.metadata.get("selection_reason") or "Qualified source coverage"),
            kind=str(lead.metadata.get("kind", "development") or "development"),
            metadata=dict(lead.metadata),
        )
        if cluster.is_qualified():
            clusters.append(cluster)
    return clusters


def _recent_story_ids(config: PodcastConfig, episode_date: date) -> set[str]:
    covered: set[str] = set()
    cutoff = episode_date - timedelta(days=config.selection.recent_days)
    for path in config.outputs.manifests.glob("*.json"):
        try:
            manifest = EpisodeManifest.read(path)
            prior_date = date.fromisoformat(manifest.episode_date)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if cutoff <= prior_date < episode_date:
            covered.update(story.id for story in manifest.stories)
    return covered


def _select_stories(config: PodcastConfig, clusters: list[StoryCluster], episode_date: date) -> tuple[StoryCluster, ...]:
    recent = _recent_story_ids(config, episode_date)
    ranked = sorted(
        (cluster for cluster in clusters if cluster.id not in recent),
        key=lambda cluster: (
            -max(float(item.metadata.get("score", 0)) for item in cluster.sources),
            cluster.id,
        ),
    )
    selected: list[StoryCluster] = []
    organizations: dict[str, int] = defaultdict(int)
    categories: dict[str, int] = defaultdict(int)
    for cluster in ranked:
        organization = cluster.organization.casefold()
        category = cluster.category.casefold()
        if organization and organizations[organization] >= config.selection.max_per_organization:
            continue
        if category and categories[category] >= config.selection.max_per_category:
            continue
        selected.append(cluster)
        if organization:
            organizations[organization] += 1
        if category:
            categories[category] += 1
        if len(selected) >= config.selection.max_stories:
            break
    return tuple(selected)


def render_source_document(show_title: str, episode_date: date, stories: tuple[StoryCluster, ...]) -> str:
    lines = [f"# {show_title} — {episode_date.isoformat()}", "", "Use only the cited facts below.", ""]
    for index, story in enumerate(stories, 1):
        editorial = story.metadata.get("editorial")
        if not isinstance(editorial, dict):
            editorial = {}
        actions = editorial.get("builder_actions") or story.metadata.get("builder_actions") or []
        if isinstance(actions, (tuple, list)):
            actions_text = ", ".join(str(action) for action in actions) or "not specified"
        else:
            actions_text = str(actions)
        caveats = str(editorial.get("caveats") or story.metadata.get("caveats") or "Verify claims against the linked source; this document does not add facts beyond citations.")
        why_now = str(editorial.get("why_now") or story.metadata.get("why_now") or story.selection_reason)
        rationale = str(editorial.get("rationale") or story.selection_reason)
        depth = str(editorial.get("depth_recommendation") or story.metadata.get("depth_recommendation") or "brief")
        lines.extend(
            [
                f"## {index}. {story.title}",
                "",
                f"**What happened:** {story.summary}",
                f"**Story kind:** {story.kind}",
                f"**Builder impact:** {story.metadata.get('builder_impact', 'not scored')}",
                f"**Why now:** {why_now}",
                f"**Editorial rationale:** {rationale}",
                f"**Builder actions:** {actions_text}",
                f"**Depth:** {depth}",
                f"**Caveats / Unknowns:** {caveats}",
                "**Sources:**",
            ]
        )
        lines.extend(f"- [{source.source}]({source.url}) — {source.authority}" for source in story.sources)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def run_episode(config: PodcastConfig, episode_date: date, *, shadow: bool = False) -> EpisodeManifest | NoEpisodeResult:
    items = _load_fixture(config.source.fixture)
    stories = _select_stories(config, _cluster_items(items), episode_date)
    if len(stories) < config.selection.min_stories:
        return NoEpisodeResult(
            episode_date=episode_date,
            reason="fewer than minimum qualifying stories",
        )

    source_path = config.outputs.sources / f"{episode_date.isoformat()}.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_body = render_source_document(config.show.title, episode_date, stories)
    source_path.write_text(source_body, encoding="utf-8")

    created = datetime(
        episode_date.year,
        episode_date.month,
        episode_date.day,
        config.show.publication_hour,
        tzinfo=ZoneInfo(config.show.timezone),
    ).astimezone(UTC).isoformat().replace("+00:00", "Z")
    manifest_path = config.outputs.manifests / f"{episode_date.isoformat()}.json"
    try:
        source_document = source_path.relative_to(config.path.parent).as_posix()
    except ValueError:
        source_document = str(source_path)
    filename = f"{config.show.episode_file_prefix}_{episode_date.isoformat()}.mp3"
    episode_id = f"{config.show.episode_guid_prefix}-{episode_date.isoformat()}"
    manifest = EpisodeManifest(
        show_slug=config.show.slug,
        episode_id=episode_id,
        episode_date=episode_date.isoformat(),
        title=f"{config.show.title} — {episode_date.isoformat()}",
        created_at=created,
        stories=stories,
        source_document=source_document,
        pipeline_version=__version__,
        metadata={},
    )
    manifest.write(manifest_path)

    audio_url = config.audio.public_url_template.format(date=episode_date.isoformat(), filename=filename)
    audio_length = config.audio.fixture_length_bytes
    duration_seconds = 0.0
    duration = config.audio.duration
    if config.audio.provider == "notebooklm":
        audio_path = config.audio.output_dir / filename
        publish_audio(
            source_path,
            audio_path,
            instructions=config.audio.instructions or None,
            language=config.audio.language,
            audio_length_name=config.audio.audio_length,
            max_duration_seconds=config.audio.max_duration_seconds,
        )
        audio_length = audio_path.stat().st_size
        if audio_length < 1:
            raise RuntimeError("NotebookLM returned an empty audio file")
        duration_seconds = probe_audio_duration(audio_path)
        duration = format_duration(duration_seconds)
        if not shadow and config.publication.provider == "r2":
            publisher = R2Publisher.from_env(
                bucket=config.publication.bucket,
                endpoint_url=config.publication.endpoint_url,
                public_base_url=config.publication.public_base_url,
                access_key_env=config.publication.access_key_env,
                secret_key_env=config.publication.secret_key_env,
                max_bucket_bytes=config.publication.max_bucket_bytes,
            )
            audio_url = publisher.publish(audio_path, f"episodes/{filename}")

    if config.audio.provider != "notebooklm":
        duration = config.audio.duration
    manifest = replace(
        manifest,
        audio_url=audio_url,
        duration=duration,
        metadata={**manifest.metadata, "duration_seconds": duration_seconds},
    )
    manifest.write(manifest_path)
    if not shadow:
        write_episode(
            config.outputs.feed,
            show=config.show,
            manifest=manifest,
            audio_url=audio_url,
            audio_length=audio_length,
            duration=duration,
        )
    return manifest
