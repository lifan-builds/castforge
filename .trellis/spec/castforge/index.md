# CastForge Project Specifications

CastForge is a reusable Python framework for automated podcast pipelines. Read these specifications before changing framework code, package metadata, public show-facing contracts, or validation procedures.

## Pre-Development Checklist

1. Read [Framework and Show Ownership](framework-show-ownership.md) before changing pipeline hooks, examples, instance contracts, or publishing-related behavior.
2. Read [Python Packaging](python-packaging.md) before changing Python code, dependencies, optional integrations, or package metadata.
3. Read [Verification](verification.md) and select checks supported by the repository; do not invent undeclared test or lint gates.
4. Keep credentials, show-specific prompts and identity, private source material, generated audio, feeds, episodes, and publication artifacts outside framework specifications and commits.

## Topics

- [Framework and Show Ownership](framework-show-ownership.md) — framework/show responsibilities and stable public contracts.
- [Python Packaging](python-packaging.md) — supported Python version, setuptools build, and optional integration boundaries.
- [Verification](verification.md) — package-build validation and runtime-check exclusions.

## Quality Check

Before completing work:

- confirm framework changes remain reusable and show-specific policy stays in the show repository;
- preserve subscriber-facing URLs, GUIDs, and historical enclosure URLs when changing show-facing contracts;
- confirm optional Gemini or NotebookLM behavior has not become an implicit core requirement;
- run `python -m build` for package-affecting changes and report external integration checks as skipped unless explicitly authorized and configured;
- remove ignored build output created by validation and review the tracked diff for secrets, show-owned data, and generated publication material.
