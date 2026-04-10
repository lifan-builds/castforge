# CastForge

Open-source framework for automated podcast pipelines.

CastForge helps you build repeatable source-to-podcast workflows: extract content, shape it into episode materials, generate audio, publish artifacts, and run the whole thing on a schedule.

It is built for teams who want to open-source the automation behind a podcast without mixing that infrastructure with the show's branding, feed identity, and published assets.

## Why CastForge

Most podcast automation code is reusable.
Most podcast editorial logic is not.

CastForge separates those concerns:

- the framework repo owns orchestration, scheduling, runner automation, and shared integrations
- each show repo owns its source adapters, prompts, branding, RSS identity, and published files

This keeps infrastructure reusable while letting each podcast stay opinionated.

## What CastForge Handles

- scheduled and manual podcast runs
- multi-stage pipelines such as `extract -> select -> brief -> export -> audio -> publish -> validate`
- retry logic and idempotent job execution
- self-hosted runner workflows
- run manifests and artifact contracts
- shared integrations for LLMs, audio tools, and publishing helpers

## What Stays In A Show Repo

A show repo should keep the parts that define the podcast itself:

- source-specific extraction logic
- selection rules
- prompts and editorial templates
- branding and metadata
- RSS/feed identity
- public assets and published episode files

## Repository Model

A typical setup uses two repositories:

1. `castforge`
   The reusable framework.
2. `my-podcast`
   The show repo built on top of CastForge.

CastForge runs the automation. The show repo remains the public home of the podcast.

## Example

CastForge is being extracted from the production workflow behind `nitan-podcast`, a weekly Chinese podcast generated from hot USCardForum discussions.

In that setup:

- `castforge` will run the schedule and orchestration
- `nitan-podcast` will continue to own the feed, episode assets, prompts, and public URLs

## Core Concepts

CastForge organizes work into stages:

- `extract`
- `select`
- `brief`
- `export`
- `audio`
- `publish`
- `validate`

Each show can customize the parts it needs while reusing the same execution model.

## Instance Contract

Each show repo exposes a small configuration surface that CastForge can read. See `docs/instance-contract.md` and `examples/podcast.yaml`.

The first production instance keeps a strict public compatibility contract:

- feed URL must remain stable
- episode GUIDs must remain stable
- enclosure URLs must remain stable

That is the key to moving automation without breaking Apple Podcasts or Spotify subscribers.

## Initial Roadmap

- define the instance contract
- extract generic pipeline stages
- move workflow orchestration into this repo
- keep the show repo as the publishing surface
- add a reference show implementation

## Design Principle

**The framework should own execution.**
**The show repo should own identity.**

## Status

This repo is currently a scaffold for the extraction work. The first milestone is to move reusable automation here while preserving the existing public podcast endpoints in `nitan-podcast`.

## Contributing

Issues and PRs are welcome, especially for:

- source adapters
- publishing integrations
- workflow improvements
- documentation for show authors
- example show templates

## License

MIT
