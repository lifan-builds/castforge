# Show Configuration Contract

`podcast.yaml` is the show-owned boundary for CastForge's config-driven runner. The framework reads it; the show repository owns its values and public compatibility.

## Required sections

- `show`: identity, language, cadence, timezone, publication hour, feed/site/art URLs, and stable episode prefixes.
- `source`: the fixture or show-owned normalized-source input.
- `selection`: story count, organization/category diversity, and recent-coverage window.
- `audio`: fixture or NotebookLM provider, target duration, output path, language, length mode, and public URL template.
- `publication`: fixture or R2 publication configuration. Credentials are named by environment variable and never stored in YAML.
- `outputs`: local source, manifest, feed, and build paths.

See [`../examples/podcast.yaml`](../examples/podcast.yaml) for a runnable fixture configuration.

## Public compatibility

For a show with subscribers, these values are public API:

- feed URL;
- episode GUID prefix and date/key format;
- historical enclosure URLs;
- cover-art and site URLs referenced by directories.

Do not change them during framework migrations. CastForge same-date reruns replace an existing GUID rather than append a duplicate.

## Publication transaction

1. Collect and qualify sources.
2. Write the source document and episode manifest.
3. Generate audio.
4. Upload audio and verify its public URL, MIME type, and byte length.
5. Add the public audio identity to the manifest.
6. Atomically replace the RSS file.

Steps 3–4 may fail without changing public RSS. Shadow mode stops before public publication.
