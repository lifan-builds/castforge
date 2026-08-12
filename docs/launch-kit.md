# CastForge launch kit

Use these in order. Replace bracketed metrics only with current public evidence.

## PyPI and Nitan retrospective

CastForge 0.1.1 is now on PyPI: `pip install castforge==0.1.1`.

It grew out of 18 Nitan Podcast episodes and the less glamorous production lessons behind them: stable GUIDs, correct `audio/mpeg` enclosures, positive byte lengths, idempotent reruns, and refusing to move RSS when generation or upload is incomplete. The full retrospective is public: https://github.com/lifan-builds/nitan-podcast/blob/main/RETROSPECTIVE.md

CastForge packages those contracts into a small Python framework with fixture-backed `init`, `run`, and `validate` commands. AI Builder Brief is the second production proof and publishes its sources, manifest, transcript, and chapters.

PyPI: https://pypi.org/project/castforge/0.1.1/
Repository: https://github.com/lifan-builds/castforge

## AI Builder Brief beta

Publish only after seven reviewed shadows pass.

AI Builder Brief is a daily, source-transparent AI briefing built with CastForge. Each story needs an authoritative primary source or two credible independent reports. Every episode exposes the selected-source manifest, transcript, chapters, and stable MP3 origin. Publication fails closed if evidence, NotebookLM, transcription, R2, or public validation fails.

Architecture and source: https://github.com/lifan-builds/ai-builder-brief
Feed: https://lifan-builds.github.io/ai-builder-brief/feed.xml

## Show HN

Publish only after the public beta has reliability evidence.

Title: Show HN: CastForge – source-transparent, failure-safe podcast automation

I built CastForge after running an automated forum podcast for 18 episodes. The difficult part was not prompting an audio model; it was preserving stable podcast identity and refusing partial publication through provider failures.

CastForge is a Python framework with source/citation manifests, NotebookLM and R2 integrations, atomic RSS publication, idempotent date keys, public MIME/length validation, and a deterministic offline starter. AI Builder Brief is the second production implementation and makes its source ledger, transcript, and chapters public.

I would value feedback on the contracts and the under-20-minute starter, especially from people operating podcasts, self-hosted runners, or evidence-heavy content pipelines.

Repository: https://github.com/lifan-builds/castforge

## Channel angles

- Python: package API, protocols, PyPI trusted publishing, and fixture-backed quick start.
- Self-hosting: macOS runner, retries, R2, the 9 GB fail-closed cap, and atomic publication.
- Podcasting: GUID stability, RSS correctness, transcripts, chapters, and enclosure validation.
- NotebookLM: duration tuning by source count, temporary-source cleanup, authentication failures, and production integration fixes.

Check each community's current self-promotion rules immediately before posting. Answer technical questions directly and do not cross-post identical copy simultaneously.

## External-adopter outreach

Send individually after the public reference show has 30 successful days:

> I maintain CastForge, the open-source pipeline behind Nitan Podcast and AI Builder Brief. I am looking for one owner-operated technical community that wants a source-linked audio digest. I can help configure a pilot, but your team must explicitly approve the content use, own the show, review the editorial policy, and co-promote it. Would a short call about your forum and permission requirements be useful?

The day-90 adoption result counts only when a non-owner repository publishes three consecutive valid episodes.
