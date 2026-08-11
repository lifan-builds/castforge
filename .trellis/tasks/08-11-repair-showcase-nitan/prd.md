# Repair and showcase Nitan

## Goal

Restore verified feed items, add homepage, regression checks, and retrospective.

## Requirements

- Verify W31/W32 MP3s, release metadata, and historical source documents before restoring feed items.
- Do not synthesize or claim W23-W25 episodes that were never produced.
- Add a static landing page with playable episodes, subscription links, source links, project story, and Castforge attribution.
- Add feed/audio/release consistency regression checks while preserving every public URL/GUID invariant.
- Publish an evidence-backed retrospective and baseline metrics document.
- Pin Nitan to a released Castforge version.

## Acceptance Criteria

- [ ] W31/W32 appear in RSS only if their public audio returns `200 audio/mpeg` with a positive length.
- [ ] Existing feed/site/audio URLs and GUID formats do not change.
- [ ] The GitHub Pages root returns a working HTML page with episode playback.
- [ ] Tests fail when a verified published weekly MP3 is silently omitted from RSS.
- [ ] The retrospective distinguishes observed facts from lessons and recommendations.
