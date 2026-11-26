# CastForge

[![PyPI](https://img.shields.io/pypi/v/castforge.svg)](https://pypi.org/project/castforge/)
[![Python 3.10+](https://img.shields.io/pypi/pyversions/castforge.svg)](https://pypi.org/project/castforge/)
[![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL--3.0--only-blue.svg)](https://github.com/lifan-builds/castforge/blob/main/LICENSE)
[![Demo & Audio](https://img.shields.io/badge/demo-clifan.com%2Fcastforge-0f766e.svg)](https://clifan.com/castforge/)

Fail-closed Python framework for repeatable, source-transparent podcast pipelines.

CastForge separates reusable production mechanics from show-owned editorial policy. It gates cited sources into an auditable schema-v2 `EpisodeManifest`, generates NotebookLM audio with measured duration ceilings, uploads MP3s to Cloudflare R2 with bucket-cap and public `HEAD` verification, and updates RSS atomically by date-keyed GUID. Each show keeps its own collectors, prompts, identity, schedule, and feed.

```text
sources.json ──▶ StoryCluster Gate ──▶ Cited Markdown + EpisodeManifest (v2)
                  (primary or 2x          │
                   independent;           ├── --shadow stops here
                   min_stories check)     ▼
                                    NotebookLM Audio (MP3 duration probe + short retry)
                                          ▼
                                    Cloudflare R2 Upload (max_bucket_bytes + public HEAD)
                                          ▼
                                    Atomic RSS Upsert (date-keyed GUID; unchanged on failure)
```

## Live demos & audio

| Surface | What to inspect | Links |
| --- | --- | --- |
| **Interactive Workbench & Sample Audio** | 4-stage gate walkthrough and synthesized MP3 sample | [clifan.com/castforge](https://clifan.com/castforge/) · [sample-briefing.mp3](https://clifan.com/castforge/assets/sample-briefing.mp3) |
| **Nitan Podcast** | Production weekly show (28 published episodes) | [Show page](https://clifan.com/nitan-podcast/) · [GitHub](https://github.com/lifan-builds/nitan-podcast) · [RSS feed](https://lifan-builds.github.io/nitan-podcast/feed.xml) |
| **AI Builder Brief** | Evidence-gated daily builder show | [Show page](https://clifan.com/ai-builder-brief/) · [RSS feed](https://clifan.com/journal/ai-builder-brief/feed.xml) |

## Install

```bash
pip install castforge
```

With optional NotebookLM and Cloudflare R2 production integrations:

```bash
pip install "castforge[notebooklm,r2]"
```

Requires Python 3.10+. Core validation and offline runs need zero optional extras (`google-genai`, `notebooklm-py`, and `boto3` are imported lazily). Releases are published on [PyPI](https://pypi.org/project/castforge/) with trusted-publishing attestations (`0.1.4` is the first `AGPL-3.0-only` release).

## 30-second offline quickstart

Scaffold a fixture-backed show, generate an episode, and validate its manifest and RSS contract locally with no API keys or network calls:

```bash
mkdir my-show && cd my-show
castforge init
castforge run --config podcast.yaml --date 2026-08-11
castforge validate --config podcast.yaml --date 2026-08-11
```

Expected output:

```text
.../my-show/podcast.yaml
.../my-show/fixtures/sources.json
.../my-show/build/manifests/2026-08-11.json
CastForge validation passed
```

The starter produces three deterministic artifacts under `build/`:

- `build/sources/2026-08-11.md` — cited NotebookLM source document (`What happened`, `Why now`, `Caveats / Unknowns`, and linked sources);
- `build/manifests/2026-08-11.json` — schema-v2 `EpisodeManifest` preserving selected stories, citations, pipeline version, and audio metadata;
- `build/feed.xml` — valid podcast RSS with a positive-length `audio/mpeg` enclosure and date-keyed GUID.

Replace the fixture sources and example URLs in `podcast.yaml` before production use.

## Fail-closed guarantees

- **Evidence-gated selection (`StoryCluster`):** A story qualifies only with a `primary` source, at least two distinct `independent` sources, or `expert_analysis` backed by an `analysis` source. Uncorroborated `signal` items are excluded.
- **Diversity & no-episode gating:** `max_per_organization`, `max_per_category`, and `recent_days` prevent repetition across episodes; falling below `min_stories` exits cleanly with `no-episode` instead of publishing filler.
- **Duration ceiling & retry:** Measures generated MP3 length, retries once at NotebookLM `short` length if it exceeds `max_duration_seconds`, and fails closed if still over ceiling.
- **Capacity-checked R2 + atomic RSS:** Paginates the bucket to enforce `max_bucket_bytes` (subtracting overwritten object sizes), uploads as `audio/mpeg`, verifies the public URL via `HEAD` (status, MIME type, exact byte length, portable `certifi` CAs), and only then atomically replaces the RSS file. Any failed stage leaves the existing feed unchanged.

## Core contracts

```python
from castforge import EpisodeManifest, SourceItem, StoryCluster
```

- `SourceItem` normalizes one `primary`, `independent`, `analysis`, or `signal` source with ISO 8601 `published_at`.
- `StoryCluster` deduplicates related coverage and enforces source qualification.
- `EpisodeManifest` records the selected stories, citations, source document path, pipeline version, and public audio identity.

The generic CLI consumes `podcast.yaml` (see [Show Configuration Contract](https://github.com/lifan-builds/castforge/blob/main/docs/instance-contract.md)); show-specific collectors and ranking stay in the show repository.

## Commands

```bash
castforge init [directory]
castforge run --config podcast.yaml --date YYYY-MM-DD [--shadow]
castforge validate --config podcast.yaml [--date YYYY-MM-DD] [--check-public]
```

`--shadow` generates the source document and manifest without mutating RSS or R2. Same-date production reruns upsert the date-keyed RSS item by GUID instead of duplicating it.

## Production configuration

See [`examples/podcast.yaml`](https://github.com/lifan-builds/castforge/blob/main/examples/podcast.yaml) for the complete schema.

### NotebookLM audio

```yaml
audio:
  provider: notebooklm
  output_dir: build/audio
  duration: 00:06:00
  public_url_template: https://audio.example.com/episodes/{filename}
  language: en
  audio_length: short
  max_duration_seconds: 900
```

Install and authenticate once on the runner:

```bash
pip install "castforge[notebooklm]"
playwright install chromium
notebooklm login
```

Set `NOTEBOOKLM_NOTEBOOK_ID`. Authentication state and notebook ownership stay outside the show repository.

### Cloudflare R2 publication

```yaml
publication:
  provider: r2
  bucket: podcast-audio
  endpoint_url: https://ACCOUNT_ID.r2.cloudflarestorage.com
  public_base_url: https://audio.example.com
  access_key_env: R2_ACCESS_KEY_ID
  secret_key_env: R2_SECRET_ACCESS_KEY
  download_url_prefix: https://op3.dev/e/
  max_bucket_bytes: 9000000000
```

Optional privacy-respecting download redirects such as OP3 are applied only after the R2 origin passes public `HEAD` validation.

## Existing hook pipeline

Shows migrating to config-driven artifacts can wire show-specific extraction and publishing through `PipelineHooks`:

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

Tests run offline against fake provider clients. Live NotebookLM and R2 checks require explicit credentials and are outside the default suite.

## License

Open source under [AGPL-3.0-only](https://github.com/lifan-builds/castforge/blob/main/LICENSE), with the Section 7 attribution terms in [ATTRIBUTION.md](https://github.com/lifan-builds/castforge/blob/main/ATTRIBUTION.md). Copies and modified versions must keep this credit in their README and `--version` or About output, mark their changes, and may not use the CastForge name:

> Based on CastForge by lifan-builds (https://github.com/lifan-builds/castforge)

Copyright © 2026 [lifan-builds](https://github.com/lifan-builds). Pull requests are welcome under [CONTRIBUTING.md](https://github.com/lifan-builds/castforge/blob/main/CONTRIBUTING.md) with a one-time [CLA](https://github.com/lifan-builds/castforge/blob/main/CLA.md). For licensing outside AGPL, open an issue.
