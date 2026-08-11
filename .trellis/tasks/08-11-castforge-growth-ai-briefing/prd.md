# Castforge growth and AI briefing

## Goal

Turn Castforge into a release-ready framework and prove it with both the existing Nitan Podcast and a new, source-transparent daily English show, AI Builder Brief.

## Background

- Nitan is the production case study but has public-surface, feed-consistency, and discoverability gaps.
- Castforge is used in production but is not installable from PyPI, has no framework-owned tests, and exposes weekly/Chinese assumptions.
- AI Builder Brief must publish a fully automated seven-day, roughly six-minute NotebookLM dialogue from attributable AI sources, with MP3s hosted in Cloudflare R2.

## Requirements

- Productize Castforge before public promotion, preserving Nitan's subscriber-facing URLs and GUIDs.
- Repair and showcase Nitan without fabricating episodes that were never produced.
- Create AI Builder Brief as a separate public reference-show repository.
- Publish only source-qualified, fully validated episodes; failures must leave RSS unchanged.
- Add source manifests, transcripts, chapters, and Castforge attribution to the new show.
- Keep Reddit ingestion, bilingual feeds, paid promotion, sponsorships, and multiple additional shows out of scope.

## Acceptance Criteria

- [ ] Castforge is installable from PyPI, exposes a working CLI, owns deterministic tests, and can publish to R2.
- [ ] Nitan has a working landing page, verified feed/audio consistency, restored valid missing items, and an evidence-backed retrospective.
- [ ] AI Builder Brief can complete a fixture-backed run and a fail-closed production run for a date without duplicate publication.
- [ ] Cross-repository tests confirm Nitan compatibility and the new show's RSS/audio/source-manifest contracts.
- [ ] Promotion artifacts and KPI definitions are present without posting externally before the products are ready.
