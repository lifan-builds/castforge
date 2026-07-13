# Verification

The repository declares package building as its native maintenance check:

```bash
python -m build
```

For package-affecting changes, run the build and report its actual result. Build output under `build/`, `dist/`, and `*.egg-info/` is generated and ignored; remove only output created by the validation run without treating it as source.

No repository test or lint suite is declared. Do not claim tests or lint passed, and do not add or invent such checks solely for workflow migration.

Gemini, NotebookLM, browser, network, feed, audio, and publication checks require external credentials or runtime state and are not part of routine migration validation. Run them only when a task explicitly requires and authorizes them. Never read or commit credentials, provider state, private source material, generated audio, feeds, episodes, or publication artifacts as validation evidence.
