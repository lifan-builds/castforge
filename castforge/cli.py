"""Command-line interface for config-driven CastForge shows."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from castforge.config import load_config
from castforge.runner import run_episode
from castforge.scaffold import initialize_show
from castforge.validation import validate_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="castforge", description="Build source-transparent podcast pipelines")
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
            manifest = run_episode(config, args.episode_date, shadow=args.shadow)
            print(config.outputs.manifests / f"{manifest.episode_date}.json")
            return 0
        if args.command == "validate":
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
    raise AssertionError(f"unhandled command: {args.command}")
