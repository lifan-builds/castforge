# Design

The parent task coordinates three child deliverables. Castforge owns reusable contracts and integrations. Nitan remains a show-owned repository with stable public endpoints. AI Builder Brief is a second show repository that consumes a released Castforge version and stores daily MP3s in R2.

The integration boundary is artifact-based: a source collection becomes normalized source items, deduplicated story clusters, an episode manifest and NotebookLM source document, then audio, transcript/chapters, RSS, and a site. Publication is atomic after public audio validation.

No compatibility shim is required for unreleased Castforge APIs; update Nitan and the new show together. Existing Nitan feed URLs, enclosure paths, and GUIDs remain unchanged.
