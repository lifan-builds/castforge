# Design

## Boundaries

- `models.py` owns normalized source, story, and episode-manifest data.
- `contracts.py` owns small runtime-checkable protocols for collection, audio, and publication.
- `config.py` loads YAML into explicit dataclasses and rejects incomplete public contracts.
- `runner.py` performs date-keyed, fail-closed artifact generation.
- `publishers/r2.py` performs S3-compatible upload plus public HEAD validation.
- `cli.py` exposes init, run, and validate; `__main__.py` delegates to it.

The initial generic runner supports fixture/RSS-style source items and artifact generation. Show-specific ranking and rendering remain injected callables rather than a plugin registry. NotebookLM remains an optional dependency. R2 remains an optional `r2` extra.

The existing `PipelineHooks` entry point remains until Nitan is migrated in the sibling task. Weekly helper names become neutral where they are internal; public Nitan behavior stays stable.
