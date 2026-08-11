# Implementation

1. Add models, protocols, YAML config loading, and unit tests.
2. Add deterministic runner, manifest/RSS artifact generation, and idempotency tests.
3. Add R2 publishing and validation with fake-client tests.
4. Replace the CLI placeholder with init/run/validate and add fresh-wheel smoke coverage.
5. Make NotebookLM prompts/config show-neutral and keep cleanup behavior covered.
6. Update examples, README, package extras/entry point, and build metadata.
7. Run `python -m pytest`, `python -m build`, install the wheel in a temporary venv, and run CLI smoke checks.
