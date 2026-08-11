# Launch AI Builder Brief

## Goal

Create the source-transparent daily AI briefing reference show.

## Requirements

- Create a separate English reference show powered by the released Castforge package.
- Collect a rolling 24-hour window from approved primary, research, trend, and corroboration sources; exclude Reddit and newsletter-derived factual claims.
- Require a primary source or two independent credible reports for every selected story.
- Deduplicate recent coverage, cap organization/category repetition, and publish a transparent episode manifest.
- Generate a short English NotebookLM dialogue, transcript, chapters, RSS, and static site.
- Upload audio to Cloudflare R2 and publish atomically after public validation.
- Run seven days with three daily retry windows and idempotent date keys; support a non-publishing shadow mode.

## Acceptance Criteria

- [x] Fixture mode creates a cited manifest, source document, feed, transcript fixture, chapters, and site without network access.
- [x] Same-date retries create at most one RSS item and one public object key.
- [x] Unqualified stories and duplicate clusters are excluded deterministically.
- [x] Audio/upload/public-HEAD failures leave the feed and site unchanged.
- [x] Production config targets R2 with `audio/mpeg` and stable date-keyed URLs.
- [x] Shadow mode exercises the complete pipeline without mutating public storage or RSS.
