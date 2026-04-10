"""NotebookLM-facing export helpers for CastForge pipelines."""

from __future__ import annotations

from pathlib import Path

DEFAULT_EXPORT_DIR = Path("exports")
DEFAULT_MARKDOWN_NAME = "weekly_meika_notebooklm.md"


def export_for_notebooklm(
    markdown_body: str,
    export_dir: Path | None = None,
    filename: str = DEFAULT_MARKDOWN_NAME,
) -> Path:
    """Create export_dir if needed, write markdown_body as UTF-8, return absolute path."""
    out_dir = export_dir if export_dir is not None else DEFAULT_EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = (out_dir / filename).resolve()
    path.write_text(markdown_body, encoding="utf-8", newline="\n")
    return path
