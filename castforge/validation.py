"""Local and optional public validation for CastForge show artifacts."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from castforge.config import PodcastConfig
from castforge.models import EpisodeManifest
from castforge.publishers.r2 import validate_public_audio


def validate_project(config: PodcastConfig, *, episode_date: str | None = None, check_public: bool = False) -> list[str]:
    errors: list[str] = []
    manifests = (
        [config.outputs.manifests / f"{episode_date}.json"]
        if episode_date
        else sorted(config.outputs.manifests.glob("*.json"))
    )
    if not manifests:
        errors.append("no episode manifests found")
    for path in manifests:
        try:
            manifest = EpisodeManifest.read(path)
        except (OSError, ValueError) as error:
            errors.append(f"invalid manifest {path}: {error}")
            continue
        source_path = Path(manifest.source_document)
        if not source_path.is_absolute():
            source_path = config.path.parent / source_path
        if not source_path.is_file() or not source_path.read_text(encoding="utf-8").strip():
            errors.append(f"missing source document for {manifest.episode_id}: {source_path}")

    if not config.outputs.feed.is_file():
        errors.append(f"feed not found: {config.outputs.feed}")
        return errors
    try:
        root = ET.parse(config.outputs.feed).getroot()
    except ET.ParseError as error:
        errors.append(f"invalid RSS XML: {error}")
        return errors
    guids: set[str] = set()
    for item in root.findall("./channel/item"):
        guid = (item.findtext("guid") or "").strip()
        enclosure = item.find("enclosure")
        if not guid or guid in guids:
            errors.append(f"missing or duplicate GUID: {guid!r}")
        guids.add(guid)
        if enclosure is None:
            errors.append(f"missing enclosure for {guid}")
            continue
        url = enclosure.get("url", "")
        try:
            length = int(enclosure.get("length", "0"))
        except ValueError:
            length = 0
        if length < 1:
            errors.append(f"non-positive enclosure length for {guid}")
        if enclosure.get("type") != "audio/mpeg":
            errors.append(f"wrong enclosure type for {guid}")
        if check_public and url:
            try:
                validate_public_audio(url, expected_length=length)
            except Exception as error:
                errors.append(f"public audio validation failed for {guid}: {error}")
    return errors
