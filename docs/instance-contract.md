# Instance Contract

CastForge expects each show repository to expose a small, stable contract that describes:

- who the podcast is
- which public URLs must remain unchanged
- where published artifacts live
- which adapters and templates CastForge should call

The initial contract format is YAML. A reference example lives at `examples/podcast.yaml`.

## Required Fields

### `metadata`

Describes the show identity.

- `slug`
- `displayName`
- `language`
- `description`

### `publicContract`

Defines subscriber-facing values that must not drift across migrations.

- `siteUrl`
- `feedUrl`
- `audioBaseUrl`
- `coverArtUrl`
- `episodeFilePrefix`
- `episodeGuidPrefix`
- `publishPaths.feed`
- `publishPaths.audioDir`

### `source`

Defines the extraction adapter and how CastForge should configure it.

### `editorial`

Defines the default editorial pipeline for the show.

### `outputs`

Defines where markdown, releases, forum drafts, and validators live in the show repo.

## Compatibility Rules

For any podcast that already has subscribers:

- do not change the feed URL
- do not change the GUID prefix or GUID format
- do not change historical enclosure URLs
- do not move public MP3 files without preserving the old URLs

Those are not internal details. They are part of the show's public API.

## Execution Model

The intended workflow is:

1. CastForge checks out the show repo.
2. CastForge reads `podcast.yaml`.
3. CastForge executes the pipeline using the configured adapters and templates.
4. CastForge writes updated artifacts back into the show repo.
5. The show repo remains the public publishing surface.
