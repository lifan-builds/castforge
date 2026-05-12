"""Reusable Gemini briefing step for CastForge pipelines."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是播客来源文档编辑，正在把抓取到的论坛素材整理成供音频生成工具使用的中文 Markdown。

请输出**事实优先、来源约束清晰**的结构化 Markdown。要求：
- 如果输入已经包含 Story Brief、What Happened、Evidence From Source、Informative Replies、Caveats / Unknowns、Editorial Voice 等结构，保留并强化这些结构，不要改写成纯评论稿。
- 每个话题先讲清楚事实：发生了什么、必要背景、来源里明确给出的数字/日期/限制/项目名/具体说法。
- 社区回复只能作为信息、修正、数据点或分歧使用；不要让玩笑、情绪化短评或高赞吐槽盖过事实。
- 对缺失背景、YMMV、争议点、未经验证的说法要明确标注，不要替来源补全不存在的因果。
- 保留论坛常用术语与梗（如 5/24、杀全家、史高、冥币）的原样表述，但先解释必要上下文。
- 语气可以生动，但不要为了戏剧性牺牲准确性；不要写双人对话脚本，不要分配主持人台词。

直接输出 Markdown 正文，不要外层代码块标记。"""


def write_briefing_markdown(raw_extraction_text: str) -> str:
    """Call Gemini with UTF-8; return a single Markdown document for upload."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required when briefing is enabled")

    from google import genai

    model_id = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()
    client = genai.Client(api_key=api_key)

    user_part = f"以下是需要整理的原始素材（可为结构化列表或长文本）：\n\n{raw_extraction_text}"
    logger.info("Calling Gemini model=%r for briefing", model_id)
    response = client.models.generate_content(
        model=model_id,
        contents=[SYSTEM_PROMPT, user_part],
        config=genai.types.GenerateContentConfig(temperature=0.5),
    )

    text = response.text or ""
    if not text.strip():
        raise RuntimeError("Gemini returned empty briefing text")
    return text.strip()
