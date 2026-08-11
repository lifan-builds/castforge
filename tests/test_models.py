from __future__ import annotations

from castforge.models import EpisodeManifest, SourceItem, StoryCluster


def _source(*, source: str = "Acme", authority: str = "primary") -> SourceItem:
    return SourceItem(
        id=f"{source}-1",
        title="A release",
        url="https://example.com/release",
        source=source,
        published_at="2026-08-11T12:00:00Z",
        summary="A documented release happened.",
        authority=authority,
    )


def test_primary_source_qualifies_story() -> None:
    story = StoryCluster(
        id="release",
        title="A release",
        summary="A documented release happened.",
        category="models",
        organization="Acme",
        sources=(_source(),),
        selection_reason="Primary release",
    )
    assert story.is_qualified()


def test_two_independent_sources_qualify_story() -> None:
    story = StoryCluster(
        id="reported",
        title="Reported development",
        summary="Two publications independently reported it.",
        category="industry",
        organization="Acme",
        sources=(
            _source(source="Publisher A", authority="independent"),
            _source(source="Publisher B", authority="independent"),
        ),
        selection_reason="Independent corroboration",
    )
    assert story.is_qualified()


def test_manifest_json_round_trip(tmp_path) -> None:
    story = StoryCluster(
        id="release",
        title="A release",
        summary="A documented release happened.",
        category="models",
        organization="Acme",
        sources=(_source(),),
        selection_reason="Primary release",
    )
    manifest = EpisodeManifest(
        show_slug="show",
        episode_id="show-2026-08-11",
        episode_date="2026-08-11",
        title="Show — 2026-08-11",
        created_at="2026-08-11T13:00:00Z",
        stories=(story,),
        source_document="build/sources/2026-08-11.md",
        pipeline_version="0.1.0",
        transcript_url="https://example.com/transcript.vtt",
        chapters_url="https://example.com/chapters.json",
    )
    path = manifest.write(tmp_path / "manifest.json")
    assert EpisodeManifest.read(path) == manifest
    assert path.read_text(encoding="utf-8").endswith("\n")
