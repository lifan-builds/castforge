"""Small, provider-neutral MP3 probing helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def probe_audio_duration(path: Path) -> float:
    """Return the measured audio duration in seconds using ``ffprobe``.

    Duration is intentionally measured from the generated file rather than a
    configured target.  A missing probe binary, malformed file, or non-positive
    result is a hard failure so callers cannot publish an unverifiable episode.
    """

    audio = Path(path)
    if not audio.is_file() or audio.stat().st_size < 1:
        raise ValueError(f"audio file is missing or empty: {audio}")
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        duration = float(result.stdout.strip())
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        raise RuntimeError(f"unable to measure MP3 duration for {audio}") from error
    if duration <= 0:
        raise ValueError(f"audio duration must be positive: {audio}")
    return duration


def format_duration(seconds: float) -> str:
    """Format seconds as the podcast ``HH:MM:SS`` duration value."""

    if seconds <= 0:
        raise ValueError("duration must be positive")
    total = max(1, int(round(seconds)))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
