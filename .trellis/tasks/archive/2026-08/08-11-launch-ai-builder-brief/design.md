# Design

The show repository contains source configuration, show-specific ranking/rendering, fixtures, workflow, public site, RSS, manifests, and tests. Castforge contains reusable models, orchestration, NotebookLM, and R2 publishing.

Collectors emit normalized source items. The show clusters duplicates, applies source qualification and recent-coverage rules, chooses up to five balanced stories, and renders an attributable NotebookLM source document. Audio is generated and transcribed, then staged with RSS/site outputs. Only after R2 upload and public HEAD validation are all public files committed.

GitHub Actions covers the PST and PDT UTC ranges, then admits only 6, 8, and 10 AM in `America/Los_Angeles`. A repository variable keeps scheduled publication disabled until production shadow approval. A date-keyed release marker and feed GUID make retries idempotent. Shadow mode writes artifacts only.
