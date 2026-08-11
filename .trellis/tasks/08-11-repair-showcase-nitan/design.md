# Design

Use Nitan's existing RSS generator and public-contract module. Reconstruct missing feed entries from committed source Markdown plus verified MP3 metadata, not from guessed titles or durations. Generate or maintain the landing page as a static file under `docs/`, reading the same feed contract so links cannot drift.

Add consistency coverage beside current RSS/public-contract tests. Keep all audio under the existing GitHub Pages paths.
