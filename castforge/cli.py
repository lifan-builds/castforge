# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lifan-builds. CastForge; Section 7 attribution terms in ATTRIBUTION.md.
"""Command-line interface for config-driven CastForge shows."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from castforge import ATTRIBUTION, __version__
from castforge.config import load_config
from castforge.runner import NoEpisodeResult, run_episode
from castforge.scaffold import initialize_show
from castforge.validation import validate_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="castforge",
        description="Build source-transparent podcast pipelines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"castforge {__version__}\n{ATTRIBUTION}\nLicense: AGPL-3.0-only with Section 7 attribution terms (ATTRIBUTION.md)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create a minimal show repository")
    init_parser.add_argument("directory", nargs="?", type=Path, default=Path.cwd())

    run_parser = subparsers.add_parser("run", help="run one date-keyed episode")
    run_parser.add_argument("--config", type=Path, default=Path("podcast.yaml"))
    run_parser.add_argument("--date", dest="episode_date", type=date.fromisoformat, default=date.today())
    run_parser.add_argument("--shadow", action="store_true", help="generate artifacts without publishing RSS or R2")

    validate_parser = subparsers.add_parser("validate", help="validate manifests, RSS, and optional public audio")
    validate_parser.add_argument("--config", type=Path, default=Path("podcast.yaml"))
    validate_parser.add_argument("--date", dest="episode_date", default=None)
    validate_parser.add_argument("--check-public", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            for path in initialize_show(args.directory):
                print(path)
            return 0
        config = load_config(args.config)
        if args.command == "run":
            result = run_episode(config, args.episode_date, shadow=args.shadow)
            if isinstance(result, NoEpisodeResult):
                print(result.status)
            else:
                print(config.outputs.manifests / f"{result.episode_date}.json")
            return 0
        errors = validate_project(
            config,
            episode_date=args.episode_date,
            check_public=args.check_public,
        )
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print("CastForge validation passed")
        return 0
    except Exception as error:
        logging.getLogger("castforge").error("%s", error)
        return 1
