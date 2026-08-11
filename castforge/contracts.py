"""Small extension contracts for show-owned CastForge integrations."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from castforge.models import SourceItem


@runtime_checkable
class SourceAdapter(Protocol):
    def collect(self, start: datetime, end: datetime) -> list[SourceItem]: ...


@runtime_checkable
class AudioProvider(Protocol):
    def generate(self, source_document: Path, output_audio: Path) -> Path: ...


@runtime_checkable
class Publisher(Protocol):
    def publish(self, local_audio: Path, object_key: str) -> str: ...
