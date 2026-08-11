# Productize Castforge

## Goal

Release-ready framework contracts, CLI, tests, R2 publishing, and PyPI packaging.

## Background

Castforge 0.1.0 currently has hook-based orchestration and NotebookLM/Gemini helpers, but `python -m castforge` is a placeholder, the reusable defaults are weekly and Chinese, no tests are owned by this repository, and the package is not on PyPI.

## Requirements

- Add normalized `SourceItem`, `StoryCluster`, and `EpisodeManifest` models with stable JSON serialization.
- Add minimal `SourceAdapter`, `AudioProvider`, and `Publisher` protocols and retain the existing hook pipeline only where Nitan still consumes it.
- Implement `castforge init`, `castforge run --config ... --date ...`, and `castforge validate`.
- Add config-driven cadence, timezone, language, prompts, episode identity, source fixtures, and output paths.
- Provide NotebookLM audio generation with configurable English/Chinese instructions and guaranteed temporary-source cleanup.
- Provide an S3-compatible R2 publisher that verifies positive content length and `audio/mpeg` before reporting success.
- Add deterministic offline tests and a fixture-backed example through manifest and RSS generation.
- Publish package metadata and docs suitable for PyPI, without embedding show-specific branding.

## Acceptance Criteria

- [ ] `python -m pytest` passes without network access.
- [ ] A fresh Python 3.10+ environment installs the built wheel and all three CLI commands execute.
- [ ] `castforge run` creates deterministic manifest/source/RSS artifacts from a fixture.
- [ ] A failed audio/upload/validation stage cannot mutate the configured public feed.
- [ ] Same-date reruns do not duplicate an episode.
- [ ] R2 upload validation rejects missing, zero-length, or wrong-MIME audio.
- [ ] Nitan's existing hook-based entry point remains functional after coordinated updates.
