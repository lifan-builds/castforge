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
