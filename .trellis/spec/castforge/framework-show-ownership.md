# Framework and Show Ownership

## Framework responsibility

CastForge provides reusable pipeline execution: orchestration and stages, hook interfaces, LLM and audio integration helpers, and export utilities. Framework behavior should remain generic enough for independent shows to supply their own policy and adapters.

## Show repository responsibility

Each show repository owns its:

- source adapters and extraction logic;
- prompts and editorial templates;
- identity, branding, workflow, and schedule;
- secrets and runner configuration;
- feed, episodes, generated audio, published assets, and publication policy.

Do not move concrete show identity, editorial text, schedules, credentials, feeds, episodes, or assets into CastForge code or Trellis specifications.

## Public compatibility contract

The instance contract describes show-owned identity and public locations. For a show with subscribers, feed URLs, episode URLs, GUID prefixes and formats, historical enclosure URLs, and existing public audio locations are public API. Preserve those values across framework or automation changes; concrete values remain owned by the show repository.

## Scenario: Temporary NotebookLM source lifecycle

### 1. Scope / Trigger

- Applies to `publish_weekly_audio_async()` whenever CastForge uploads a source into a caller-owned NotebookLM notebook.

### 2. Signatures

- Upload: `client.sources.add_file(notebook_id, markdown_path, wait=True, wait_timeout=...)`.
- Cleanup: `client.sources.delete(notebook_id, source_id)`.
- Public helper: `publish_weekly_audio_async(markdown_path, *, output_audio, ...) -> Path`.

### 3. Contracts

- The uploaded source is temporary provider state, not a show-owned archive.
- After `add_file()` returns a source ID, CastForge must attempt deletion in `finally`, after download on success and after any later generation/download error.
- Cleanup failure is logged with traceback but does not replace the primary pipeline result or invalidate an already downloaded MP3.
- Notebook ID and authentication state remain caller-owned environment/provider configuration and must never be logged as credentials or committed.

### 4. Validation & Error Matrix

| Condition | Required behavior |
| --- | --- |
| Upload fails before source ID | Propagate upload error; no delete call |
| Index/generation/download fails after source ID | Attempt delete, then preserve primary error |
| Download succeeds | Delete source, return output path |
| Delete fails after successful download | Log warning; return downloaded output path |

### 5. Good/Base/Bad Cases

- Good: one source is uploaded, audio is downloaded, and that source is deleted.
- Base: upload is rejected before a source exists, so the provider error propagates directly.
- Bad: retaining every weekly source until the notebook reaches its tier limit and all future audio jobs fail.

### 6. Tests Required

- A fake client check must assert deletion is the last provider call on both successful download and post-upload failure.
- Package changes must pass `python -m build`; live NotebookLM checks remain task-authorized only.

### 7. Wrong vs Correct

```python
# Wrong: provider state grows forever.
source = await client.sources.add_file(notebook_id, markdown_path)
await client.artifacts.download_audio(notebook_id, output_path)

# Correct: reclaim the caller notebook slot on every post-upload path.
source_id = None
try:
    source = await client.sources.add_file(notebook_id, markdown_path)
    source_id = source.id
    await client.artifacts.download_audio(notebook_id, output_path)
finally:
    if source_id:
        await client.sources.delete(notebook_id, source_id)
```
