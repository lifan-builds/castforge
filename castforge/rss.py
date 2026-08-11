"""Small RSS 2.0 writer for config-driven CastForge shows."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import UTC, datetime, time
from email.utils import format_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from castforge.config import ShowConfig
from castforge.models import EpisodeManifest

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM_NS = "http://www.w3.org/2005/Atom"
PODCAST_NS = "https://podcastindex.org/namespace/1.0"
ET.register_namespace("itunes", ITUNES_NS)
ET.register_namespace("atom", ATOM_NS)
ET.register_namespace("podcast", PODCAST_NS)


def _sub(parent: ET.Element, tag: str, text: str) -> ET.Element:
    element = ET.SubElement(parent, tag)
    element.text = text
    return element


def _new_feed(show: ShowConfig) -> tuple[ET.Element, ET.Element]:
    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    _sub(channel, "title", show.title)
    _sub(channel, "link", show.site_url)
    _sub(channel, "description", show.description)
    _sub(channel, "language", show.language)
    ET.SubElement(
        channel,
        f"{{{ATOM_NS}}}link",
        {"href": show.feed_url, "rel": "self", "type": "application/rss+xml"},
    )
    _sub(channel, f"{{{ITUNES_NS}}}author", show.author)
    _sub(channel, f"{{{ITUNES_NS}}}summary", show.description)
    ET.SubElement(channel, f"{{{ITUNES_NS}}}image", {"href": show.cover_art_url})
    ET.SubElement(channel, f"{{{ITUNES_NS}}}category", {"text": "Technology"})
    return root, channel


def _description(manifest: EpisodeManifest) -> str:
    lines = [story.summary for story in manifest.stories]
    lines.append("Sources:")
    for story in manifest.stories:
        lines.extend(f"{item.source}: {item.url}" for item in story.sources)
    return "\n\n".join(lines)


def write_episode(
    path: Path,
    *,
    show: ShowConfig,
    manifest: EpisodeManifest,
    audio_url: str,
    audio_length: int,
    duration: str,
) -> Path:
    """Atomically insert or replace one date-keyed episode."""
    if audio_length < 1:
        raise ValueError("audio_length must be positive")
    if not audio_url.strip():
        raise ValueError("audio_url is required")

    path = Path(path)
    if path.is_file():
        root = ET.parse(path).getroot()
        channel = root.find("channel")
        if channel is None:
            raise ValueError("RSS feed is missing channel")
    else:
        root, channel = _new_feed(show)

    for old in list(channel.findall("item")):
        if old.findtext("guid") == manifest.episode_id:
            channel.remove(old)

    item = ET.Element("item")
    _sub(item, "title", manifest.title)
    _sub(item, "description", _description(manifest))
    _sub(item, "guid", manifest.episode_id).set("isPermaLink", "false")
    published = datetime.combine(
        datetime.fromisoformat(manifest.episode_date).date(),
        time(hour=show.publication_hour),
        tzinfo=ZoneInfo(show.timezone),
    ).astimezone(UTC)
    _sub(item, "pubDate", format_datetime(published, usegmt=True))
    ET.SubElement(
        item,
        "enclosure",
        {"url": audio_url, "length": str(audio_length), "type": "audio/mpeg"},
    )
    _sub(item, f"{{{ITUNES_NS}}}duration", duration)
    _sub(item, f"{{{ITUNES_NS}}}summary", _description(manifest))
    if manifest.transcript_url:
        ET.SubElement(
            item,
            f"{{{PODCAST_NS}}}transcript",
            {"url": manifest.transcript_url, "type": "text/vtt"},
        )
    if manifest.chapters_url:
        ET.SubElement(
            item,
            f"{{{PODCAST_NS}}}chapters",
            {"url": manifest.chapters_url, "type": "application/json+chapters"},
        )

    first_item = next((index for index, child in enumerate(channel) if child.tag == "item"), len(channel))
    channel.insert(first_item, item)
    ET.indent(root, space="  ")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    ET.ElementTree(root).write(temporary, encoding="utf-8", xml_declaration=True)
    temporary.replace(path)
    return path
