# Artifact and Publication Contract

## Scenario: Config-driven episode publication

### 1. Scope / Trigger

- Applies to `castforge run` and show-owned pipelines using `SourceItem`, `StoryCluster`, `EpisodeManifest`, NotebookLM, RSS, or `R2Publisher`.

### 2. Signatures

- `SourceAdapter.collect(start: datetime, end: datetime) -> list[SourceItem]`
- `AudioProvider.generate(source_document: Path, output_audio: Path) -> Path`
- `Publisher.publish(local_audio: Path, object_key: str) -> str`
- `castforge run --config podcast.yaml --date YYYY-MM-DD [--shadow]`
- `castforge validate --config podcast.yaml [--date YYYY-MM-DD] [--check-public]`

### 3. Contracts

- `SourceItem.authority` is `primary`, `independent`, or `signal` and `published_at` is ISO 8601.
- A `StoryCluster` qualifies only with at least one primary source or two differently named independent sources. Signal-only clusters never publish.
- `EpisodeManifest` JSON uses stable sorted serialization and carries story citations, source document, pipeline version, audio URL, duration, and optional transcript/chapter URLs.
- NotebookLM, R2, and credentials remain optional/show-owned. Core fixture execution is offline.
- R2 credentials come from configured environment-variable names. The upload uses `audio/mpeg`; the public origin must return `200`, the same MIME, and the exact positive byte length before RSS changes.
- An analytics redirect may wrap the validated origin URL only after origin validation.
- Date-keyed GUID replacement makes reruns idempotent. RSS is the public commit point and moves last.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Missing required config or invalid timezone | Refuse to run before artifact mutation |
| Signal-only or uncorroborated story | Exclude it; fail if no qualified stories remain |
| NotebookLM failure | Preserve source/debug artifacts; do not upload or change RSS |
| Empty/non-MP3 local audio | Refuse R2 upload |
| R2/public status, MIME, or length mismatch | Raise; leave RSS unchanged |
| Same date already has a positive enclosure | Skip or replace the same GUID; never append a duplicate |
| `--shadow` | Create local artifacts without public storage/RSS mutation |

### 5. Good/Base/Bad Cases

- Good: cited stories produce audio; R2 origin validates; manifest gains transcript/chapter URLs; RSS is atomically replaced.
- Base: fixture mode produces deterministic manifest/source/RSS artifacts without provider dependencies.
- Bad: treating trend score as factual qualification or writing an enclosure before public audio validation.

### 6. Tests Required

- Model JSON round-trip and qualification assertions.
- Fixture `init → run → validate` with same-date idempotency.
- Provider failure leaves an existing feed byte-for-byte unchanged.
- Fake R2 client asserts `audio/mpeg`; fake public response covers wrong MIME and length.
- NotebookLM fake asserts temporary-source deletion is the last provider call on success and post-upload failure.
- Fresh-wheel CLI smoke after `python -m build`.

### 7. Wrong vs Correct

```python
# Wrong: a popular link becomes a fact and RSS predicts a future object.
stories = [signal_only_item]
write_feed(audio_url=predicted_url, length=0)

# Correct: qualify evidence, validate immutable audio, then commit RSS.
if story.is_qualified():
    origin = publisher.publish(local_mp3, object_key)
    write_episode(audio_url=download_prefix + origin, audio_length=local_mp3.stat().st_size)
```
