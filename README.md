# CastForge

Open-source framework for automated podcast pipelines.

CastForge helps you build repeatable source-to-podcast workflows: extract content, shape it into episode materials, generate audio, publish artifacts, and run the whole thing on a schedule.

## Why CastForge

Most podcast automation code is reusable.
Most podcast editorial logic is not.

CastForge separates those concerns:

- `CastForge` provides reusable pipeline stages, LLM integrations, audio tooling, and export helpers
- each show repo keeps its own source adapters, prompts, branding, scheduling, RSS identity, and published assets

This keeps the framework generic while letting each podcast stay opinionated.

## How It Works

CastForge is a Python package that your podcast repo depends on.

Your show repo owns:

- its GitHub Actions workflow and cron schedule
- its secrets and runner configuration
- its source extraction logic
- its prompts and editorial templates
- its published feed, episodes, and assets

CastForge provides:

- reusable pipeline orchestration
- LLM briefing helpers (Gemini)
- audio generation integration (NotebookLM)
- Markdown export utilities
- a hooks-based pipeline model so each show can plug in its own logic

## Quick Start

In your podcast repository:

```bash
pip install git+https://github.com/lifan-builds/castforge.git
```

### Optional extras

CastForge core depends only on `anyio` and `python-dotenv`. Integrations are optional:

```bash
# Gemini briefing (`castforge.briefing`)
pip install "castforge[gemini] @ git+https://github.com/lifan-builds/castforge.git"

# NotebookLM audio (`castforge.notebooklm_audio`)
pip install "castforge[notebooklm] @ git+https://github.com/lifan-builds/castforge.git"

# Both
pip install "castforge[gemini,notebooklm] @ git+https://github.com/lifan-builds/castforge.git"
```

After CastForge is published to PyPI, replace the git URL with `castforge` and the same extras.

Then write a thin `run_pipeline.py` that wires your show-specific hooks into the CastForge pipeline:

```python
from castforge.pipeline import PipelineHooks, main as castforge_main
from my_show.extractor import extract, fetch_details, list_tools, select, to_markdown
from my_show.publisher import write_post
from my_show.rss import generate_feed
from my_show.config import EPISODE_PREFIX, episode_filename, episode_url

def main(argv=None):
    hooks = PipelineHooks(
        extract_weekly_key_info=extract,
        fetch_thread_details=fetch_details,
        list_mcp_tools=list_tools,
        select_threads=select,
        threads_to_source_markdown=to_markdown,
        write_forum_post=write_post,
        generate_rss_feed=generate_feed,
        episode_file_prefix=EPISODE_PREFIX,
        week_episode_filename=episode_filename,
        week_episode_url=episode_url,
    )
    return castforge_main(argv, hooks=hooks)

if __name__ == "__main__":
    raise SystemExit(main())
```

## Pipeline Stages

CastForge organizes work into stages:

- `extract` — fetch source content via your adapter
- `select` — choose items for the episode
- `brief` — optionally rewrite/shape material with an LLM
- `export` — produce a source document for the audio engine
- `audio` — generate podcast audio (NotebookLM integration included)
- `publish` — create downstream outputs (RSS, forum posts, release artifacts)
- `validate` — run post-publish checks

Each stage is customizable through the `PipelineHooks` interface.

## Instance Contract

Each show repo can expose a `podcast.yaml` describing its identity and public URLs. See `examples/podcast.yaml` for the format.

The key rule: subscriber-facing values (feed URL, episode URLs, GUIDs) must remain stable across automation changes.

## Example Workflow

See `examples/weekly-podcast.yml` for a GitHub Actions workflow template. Copy it into your show repo and adjust the schedule, runner labels, and pipeline flags.

The key step is installing CastForge as a dependency:

```yaml
- run: $PY -m pip install -q git+https://github.com/lifan-builds/castforge.git
```

## Example

CastForge powers [`nitan-podcast`](https://github.com/lifan-builds/nitan-podcast), a weekly Chinese podcast generated from hot USCardForum discussions.

In that setup:

- `nitan-podcast` owns its workflow, schedule, feed, episodes, and public URLs
- `nitan-podcast` installs `castforge` as a dependency and delegates pipeline execution to it

## Design Principle

**The framework provides reusable execution.**
**The show repo owns identity, scheduling, and publishing.**

## Status

CastForge is being extracted from a working production podcast pipeline. The first public version includes:

- reusable pipeline stages with a hooks interface
- Gemini briefing integration
- NotebookLM audio integration
- Markdown export utilities
- instance contract documentation
- example workflow and configuration

## Contributing

Issues and PRs are welcome, especially for:

- source adapters
- publishing integrations
- new audio/LLM provider support
- documentation for show authors
- example show templates

## Publishing to PyPI (maintainers)

1. Bump `version` in `pyproject.toml`.
2. Build: `python -m pip install build twine && python -m build`.
3. Upload: `python -m twine upload dist/*` (requires a [PyPI](https://pypi.org) API token).

Until the package is on PyPI, show repos can keep installing from git as in `examples/weekly-podcast.yml`.

## License

MIT — see [LICENSE](LICENSE).
