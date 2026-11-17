# CastForge

- `castforge` is the shared Python substrate for `nitan-pod` and `ai-builder-brief`: keep show-specific collectors, editorial prompts, schedules, feeds, episodes, and credentials in the show repositories.
- Keep optional provider SDK imports (`google-genai`, `notebooklm-py`, `boto3`) lazy inside runtime call paths so core validation and offline tests require zero optional extras.
- Subscriber-facing URLs, episode GUID formats, and positive-length `audio/mpeg` enclosures are immutable public contracts; same-date reruns upsert by GUID and fail closed before mutating RSS.
