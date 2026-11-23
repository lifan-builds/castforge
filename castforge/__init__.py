# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lifan-builds. CastForge; Section 7 attribution terms in ATTRIBUTION.md.
"""Reusable contracts and orchestration for automated podcast shows."""

from castforge.models import EpisodeManifest, SourceItem, StoryCluster

__all__ = ["ATTRIBUTION", "EpisodeManifest", "SourceItem", "StoryCluster", "__version__"]

__version__ = "0.1.3"
ATTRIBUTION = "Based on CastForge by lifan-builds (https://github.com/lifan-builds/castforge)"
