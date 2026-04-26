from __future__ import annotations

"""Story2Proposal 的应用层运行入口。

这个文件负责执行一次完整运行。
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.config import DEFAULT_MODEL, OUTPUTS_DIR
from backend.domain import build_initial_context, evaluate_and_store_manuscript, persist_run_outputs
from backend.graph import build_story2proposal_graph
from backend.schemas import ResearchStory


async def run_story_to_proposal(
    story: ResearchStory,
    output_dir: Path | None = None,
    *,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """异步执行一次完整的 Story2Proposal 运行。"""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    resolved_output = output_dir or (OUTPUTS_DIR / f"{story.story_id}_{run_id}")

    # 准备本次运行的输出目录。
    resolved_output.mkdir(parents=True, exist_ok=True)
    (resolved_output / "drafts").mkdir(exist_ok=True)
    (resolved_output / "reviews").mkdir(exist_ok=True)
    (resolved_output / "rendered").mkdir(exist_ok=True)
    (resolved_output / "logs").mkdir(exist_ok=True)

    # 初始化共享状态。
    context = build_initial_context(story, resolved_output)
    graph = build_story2proposal_graph(model=model)
    try:
        await graph(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Build a structured scientific manuscript scaffold from the story in context.",
                    }
                ],
                "temperature": 0.2,
            },
            context=context,
        )
    finally:
        # 主动关闭 MCP 连接。
        await graph._mcp_manager.close()

    # 只有在最终稿生成后才执行整篇评测。
    if context.get("artifacts", {}).get("rendered") is not None:
        evaluate_and_store_manuscript(context)

    summary = persist_run_outputs(context)
    return {"context": context, "summary": summary}


def run_story_to_proposal_sync(
    story: ResearchStory,
    output_dir: Path | None = None,
    *,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """为脚本和子进程入口提供同步封装。"""
    return asyncio.run(run_story_to_proposal(story, output_dir=output_dir, model=model))
