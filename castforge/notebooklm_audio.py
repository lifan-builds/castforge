"""Reusable NotebookLM audio publishing helpers for CastForge pipelines."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import anyio

logger = logging.getLogger(__name__)

_DEFAULT_INSTRUCTIONS = """请用简体中文录制本期播客，语速偏快、节奏紧凑。

【开场格式】
不要介绍论坛或资料来源是什么。直接用一句话说明本期内容，然后快速抛出2-3个关键词作为 hook，吸引听众继续听。

【事实优先】
逐个讨论来源文档中的话题。每个话题先讲清楚 What Happened、Essential Context 和 Evidence From Source，再进入社区反应或主持人观点。听众应该在没看过原帖的情况下也能明白前因后果。

【回复使用】
如果来源文档中有 Informative Replies、精选回复或社区讨论，只引用其中提供事实、数据点、修正、约束、亲身经验或实质分歧的内容。不要把低信息量玩笑、吐槽或高赞短评当成事实主线。

【不确定性】
遇到 Caveats / Unknowns、YMMV、争议点或来源没有交代清楚的背景时，要明确说出来。不要编造缺失事实，不要不懂装懂。

【语气】
像两个熟悉主题的人聊天，不要播音腔，不要过度客套。可以有轻微调侃和个人倾向，但必须服从来源文档中的 Editorial Voice 和事实边界。"""

_INTEGRATION_HINT = (
    "Install optional deps: pip install -r requirements-integrations.txt && "
    "playwright install chromium && notebooklm login"
)


def _ensure_notebooklm_imported() -> Any:
    try:
        from notebooklm import AudioFormat, AudioLength, NotebookLMClient

        return NotebookLMClient, AudioFormat, AudioLength
    except ImportError as e:
        raise RuntimeError(
            f"notebooklm-py is not installed ({e}). {_INTEGRATION_HINT}"
        ) from e


def _parse_audio_format(name: str | None, AudioFormat: Any) -> Any:
    if not name or not str(name).strip():
        return None
    key = str(name).strip().lower().replace("-", "_")
    mapping = {
        "deep_dive": AudioFormat.DEEP_DIVE,
        "brief": AudioFormat.BRIEF,
        "critique": AudioFormat.CRITIQUE,
        "debate": AudioFormat.DEBATE,
    }
    if key not in mapping:
        raise ValueError(
            f"NOTEBOOKLM_AUDIO_FORMAT must be one of {list(mapping.keys())}, got {name!r}"
        )
    return mapping[key]


def _parse_audio_length(name: str | None, AudioLength: Any) -> Any:
    if not name or not str(name).strip():
        return None
    key = str(name).strip().lower()
    mapping = {
        "short": AudioLength.SHORT,
        "default": AudioLength.DEFAULT,
        "long": AudioLength.LONG,
    }
    if key not in mapping:
        raise ValueError(
            f"NOTEBOOKLM_AUDIO_LENGTH must be one of {list(mapping.keys())}, got {name!r}"
        )
    return mapping[key]


def _config_from_env() -> dict[str, Any]:
    notebook_id = os.environ.get("NOTEBOOKLM_NOTEBOOK_ID", "").strip()
    if not notebook_id:
        raise RuntimeError(
            "NOTEBOOKLM_NOTEBOOK_ID is required for programmatic publish "
            "(create a notebook in the UI, copy its id from the URL or metadata)."
        )
    instructions = os.environ.get("NOTEBOOKLM_AUDIO_INSTRUCTIONS", "").strip() or _DEFAULT_INSTRUCTIONS
    language = os.environ.get("NOTEBOOKLM_AUDIO_LANGUAGE", "zh").strip() or "zh"
    gen_timeout = float(os.environ.get("NOTEBOOKLM_GENERATION_TIMEOUT", "600"))
    source_wait = float(os.environ.get("NOTEBOOKLM_SOURCE_WAIT_TIMEOUT", "180"))
    storage_path = os.environ.get("NOTEBOOKLM_STORAGE_PATH", "").strip() or None
    http_timeout = float(os.environ.get("NOTEBOOKLM_HTTP_TIMEOUT", "60"))
    audio_fmt = os.environ.get("NOTEBOOKLM_AUDIO_FORMAT", "").strip() or None
    audio_len = os.environ.get("NOTEBOOKLM_AUDIO_LENGTH", "").strip() or None
    return {
        "notebook_id": notebook_id,
        "instructions": instructions,
        "language": language,
        "generation_timeout": gen_timeout,
        "source_wait_timeout": source_wait,
        "storage_path": storage_path,
        "http_timeout": http_timeout,
        "audio_format_name": audio_fmt,
        "audio_length_name": audio_len,
    }


async def publish_weekly_audio_async(
    markdown_path: Path,
    *,
    output_audio: Path,
    notebook_id: str | None = None,
    instructions: str | None = None,
    language: str | None = None,
    generation_timeout: float | None = None,
    source_wait_timeout: float | None = None,
    storage_path: str | None = None,
    http_timeout: float | None = None,
    audio_format: Any | None = None,
    audio_length: Any | None = None,
) -> Path:
    """Upload markdown, generate audio for that source, and download it."""
    NotebookLMClient, AudioFormat, AudioLength = _ensure_notebooklm_imported()
    cfg = _config_from_env()
    nb = notebook_id or cfg["notebook_id"]
    instr = instructions if instructions is not None else cfg["instructions"]
    lang = language if language is not None else cfg["language"]
    gen_to = generation_timeout if generation_timeout is not None else cfg["generation_timeout"]
    src_to = source_wait_timeout if source_wait_timeout is not None else cfg["source_wait_timeout"]
    store = storage_path if storage_path is not None else cfg["storage_path"]
    http_to = http_timeout if http_timeout is not None else cfg["http_timeout"]
    af = audio_format
    al = audio_length
    if af is None and cfg["audio_format_name"]:
        af = _parse_audio_format(cfg["audio_format_name"], AudioFormat)
    if al is None and cfg["audio_length_name"]:
        al = _parse_audio_length(cfg["audio_length_name"], AudioLength)

    md = Path(markdown_path).resolve()
    if not md.is_file():
        raise FileNotFoundError(f"Markdown export not found: {md}")

    out = Path(output_audio).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    client_ctx = await NotebookLMClient.from_storage(store, timeout=http_to)
    async with client_ctx as client:
        logger.info("NotebookLM: adding file source %s", md)
        source = await client.sources.add_file(nb, md, wait=True, wait_timeout=src_to)
        if source.is_error:
            raise RuntimeError(f"NotebookLM source failed to index: {source!r}")
        sid = source.id
        logger.info("NotebookLM: source ready id=%s, generating audio (language=%r)", sid, lang)

        status = await client.artifacts.generate_audio(
            nb,
            source_ids=[sid],
            language=lang,
            instructions=instr,
            audio_format=af,
            audio_length=al,
        )
        final = await client.artifacts.wait_for_completion(
            nb,
            status.task_id,
            timeout=gen_to,
        )
        if final.is_failed:
            raise RuntimeError(
                f"NotebookLM audio generation failed: status={final.status!r} error={final.error!r}"
            )
        if not final.is_complete:
            raise RuntimeError(f"NotebookLM audio generation ended incomplete: {final!r}")

        logger.info("NotebookLM: downloading audio to %s", out)
        await client.artifacts.download_audio(nb, str(out), artifact_id=final.task_id)
    return out


def publish_weekly_audio(
    markdown_path: Path,
    output_audio: Path,
    **kwargs: Any,
) -> Path:
    """Sync wrapper for jobs and CLI."""

    async def _runner() -> Path:
        return await publish_weekly_audio_async(
            markdown_path, output_audio=output_audio, **kwargs
        )

    return anyio.run(_runner)
