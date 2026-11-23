# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lifan-builds. CastForge; Section 7 attribution terms in ATTRIBUTION.md.
"""Module entry point for ``python -m castforge``."""

from __future__ import annotations

from castforge.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
