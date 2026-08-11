# CastForge

Open-source Python framework for repeatable, source-transparent podcast pipelines.

CastForge separates reusable production mechanics from show-owned editorial policy. It can normalize cited sources, record an auditable episode manifest, generate NotebookLM audio, publish MP3s to Cloudflare R2, update RSS atomically, and validate the result. Each show keeps its own sources, prompts, identity, schedule, and feed.

CastForge powers [Nitan Podcast](https://github.com/lifan-builds/nitan-podcast), a production Chinese podcast generated from USCardForum discussions.

## Install

The `v0.1.0` wheel is attached to the [GitHub release](https://github.com/lifan-builds/castforge/releases/tag/v0.1.0). Until the first PyPI upload is authorized, install the immutable release tag:

```bash
pip install "castforge @ git+https://github.com/lifan-builds/castforge.git@v0.1.0"

# Optional production integrations
pip install "castforge[notebooklm,r2] @ git+https://github.com/lifan-builds/castforge.git@v0.1.0"
```

Python 3.10 or newer is supported. Gemini, NotebookLM, and R2 dependencies remain optional.

## First episode in under 20 minutes

```bash
mkdir my-show && cd my-show
castforge init
castforge run --config podcast.yaml --date 2026-08-11
castforge validate --config podcast.yaml --date 2026-08-11
```

The fixture-backed starter creates:

- a cited NotebookLM source document;
- a deterministic episode manifest;
- an RSS feed with a positive audio enclosure contract.

Fixture mode does not call an LLM, audio service, or public endpoint. Replace the example sources and public values before production use.

## Core contracts

```python
from castforge import EpisodeManifest, SourceItem, StoryCluster
from castforge.contracts import AudioProvider, Publisher, SourceAdapter
```

- `SourceItem` normalizes one primary, independent, or trend-signal source.
- `StoryCluster` groups duplicate coverage and qualifies only a primary source or two independent reports.
- `EpisodeManifest` preserves the selected stories, citations, source document, pipeline version, and public audio identity.
- `SourceAdapter`, `AudioProvider`, and `Publisher` are intentionally small protocols implemented by show repositories or integrations.

The generic CLI consumes `podcast.yaml`; show-specific collectors and ranking remain in the show repository.

## Commands

```bash
castforge init [directory]
castforge run --config podcast.yaml --date YYYY-MM-DD [--shadow]
castforge validate --config podcast.yaml [--date YYYY-MM-DD] [--check-public]
```

`--shadow` creates the source and manifest artifacts but does not mutate RSS or R2. Same-date production reruns replace the date-keyed RSS item instead of duplicating it.

## Production configuration

See [`examples/podcast.yaml`](examples/podcast.yaml) for the complete schema.

For NotebookLM:

```yaml
audio:
  provider: notebooklm
  output_dir: build/audio
  duration: 00:06:00
  public_url_template: https://audio.example.com/episodes/{filename}
  language: en
  audio_length: short
```

Install and authenticate the integration once on the runner:

```bash
pip install "castforge[notebooklm]"
playwright install chromium
notebooklm login
```

Set `NOTEBOOKLM_NOTEBOOK_ID`. Authentication state and notebook ownership stay outside the show repository.

For Cloudflare R2:

```yaml
publication:
  provider: r2
  bucket: podcast-audio
  endpoint_url: https://ACCOUNT_ID.r2.cloudflarestorage.com
  public_base_url: https://audio.example.com
  access_key_env: R2_ACCESS_KEY_ID
  secret_key_env: R2_SECRET_ACCESS_KEY
  download_url_prefix: https://op3.dev/e/
```

CastForge uploads MP3s as `audio/mpeg`, then sends a public `HEAD` request and verifies status, MIME type, and byte length before updating RSS. A show may apply a privacy-respecting download redirect such as OP3 after the R2 origin passes validation. A failed generation, upload, or public check leaves the feed unchanged.

## Existing hook pipeline

Production shows can continue wiring show-specific extraction and publishing through `PipelineHooks` while migrating to config-driven artifacts:

```python
from castforge.pipeline import PipelineHooks, main as castforge_main

def main(argv=None):
    hooks = PipelineHooks(
        extract_weekly_key_info=extract,
        fetch_thread_details=fetch_details,
        list_mcp_tools=list_tools,
        select_threads=select,
        threads_to_source_markdown=to_markdown,
        write_forum_post=write_post,
        generate_rss_feed=generate_feed,
        episode_file_prefix="weekly_episode",
        week_episode_filename=episode_filename,
        week_episode_url=episode_url,
    )
    return castforge_main(argv, hooks=hooks)
```

CastForge owns execution and provider integrations. The show owns sources, editorial policy, branding, secrets, scheduling, feeds, episodes, and public compatibility.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m build
```

Tests are offline and use fake provider clients. Live NotebookLM and R2 checks require explicit credentials and are not part of the ordinary suite.

## License

MIT — see [LICENSE](LICENSE).
