# Artifact and Publication Contract

## Scenario: Config-driven episode publication

### 1. Scope / Trigger

- Applies to `castforge run` and show-owned pipelines using `SourceItem`, `StoryCluster`, `EpisodeManifest`, NotebookLM, RSS, or `R2Publisher`.

### 2. Signatures

- `SourceAdapter.collect(start: datetime, end: datetime) -> list[SourceItem]`
- `AudioProvider.generate(source_document: Path, output_audio: Path) -> Path`
- `Publisher.publish(local_audio: Path, object_key: str) -> str`
- `R2Publisher(..., max_bucket_bytes: int = 0)`
- `castforge run --config podcast.yaml --date YYYY-MM-DD [--shadow]`
- `castforge validate --config podcast.yaml [--date YYYY-MM-DD] [--check-public]`

### 3. Contracts

- `SourceItem.authority` is `primary`, `independent`, or `signal` and `published_at` is ISO 8601.
- A `StoryCluster` qualifies only with at least one primary source or two differently named independent sources. Signal-only clusters never publish.
- `EpisodeManifest` JSON uses stable sorted serialization and carries story citations, source document, pipeline version, audio URL, duration, and optional transcript/chapter URLs.
- NotebookLM, R2, and credentials remain optional/show-owned. Core fixture execution is offline.
- R2 credentials come from configured environment-variable names. The upload uses `audio/mpeg`; the public origin must return `200`, the same MIME, and the exact positive byte length before RSS changes.
- `publication.max_bucket_bytes` is non-negative. Zero disables capacity enforcement; a positive value requires a paginated bucket listing before upload. Projected usage is `bucket total - replaced object size + local file size`, so idempotent overwrites do not double count.
- A capacity failure occurs before `put_object`; it must not delete historical objects or mutate RSS.
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
| Negative `max_bucket_bytes` | Reject configuration |
| Projected R2 usage exceeds `max_bucket_bytes` | Raise before upload; leave bucket and RSS unchanged |
| Same date already has a positive enclosure | Skip or replace the same GUID; never append a duplicate |
| `--shadow` | Create local artifacts without public storage/RSS mutation |

### 5. Good/Base/Bad Cases

- Good: cited stories produce audio; R2 origin validates; manifest gains transcript/chapter URLs; RSS is atomically replaced.
- Base: fixture mode produces deterministic manifest/source/RSS artifacts without provider dependencies.
- Good capacity case: a same-key retry subtracts the old object before applying the configured ceiling.
- Bad: treating trend score as factual qualification or writing an enclosure before public audio validation.
- Bad capacity case: deleting historical enclosures to remain below a billing allowance.

### 6. Tests Required

- Model JSON round-trip and qualification assertions.
- Fixture `init → run → validate` with same-date idempotency.
- Provider failure leaves an existing feed byte-for-byte unchanged.
- Fake R2 client asserts `audio/mpeg`; fake public response covers wrong MIME and length.
- Fake R2 pages assert capacity rejection happens before `put_object`, pagination tokens are followed, and same-key replacement is subtracted.
- NotebookLM fake asserts temporary-source deletion is the last provider call on success and post-upload failure.
- Fresh-wheel CLI smoke after `python -m build`.

### 7. Wrong vs Correct

```python
# Wrong: a popular link becomes a fact and RSS predicts a future object.
stories = [signal_only_item]
write_feed(audio_url=predicted_url, length=0)

# Correct: qualify evidence, validate immutable audio, then commit RSS.
if story.is_qualified():
    publisher = R2Publisher(..., max_bucket_bytes=9_000_000_000)
    origin = publisher.publish(local_mp3, object_key)  # Capacity check precedes upload.
    write_episode(audio_url=download_prefix + origin, audio_length=local_mp3.stat().st_size)
```
