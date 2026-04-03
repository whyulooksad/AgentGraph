from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import Agent, settings


async def main() -> None:
    # Keep this demo isolated from the project's global draw.io MCP config.
    settings.mcp_servers = {}

    agent = Agent(
        name="gui_operator_v2",
        model="qwen-plus",
        instructions=(
            "You are a browser GUI agent.\n"
            "You must use Playwright MCP tools to inspect and operate the page.\n"
            "Do not claim an action succeeded unless a tool result confirms it.\n"
            "You must complete this exact workflow:\n"
            "1. Open https://example.com .\n"
            "2. Inspect the page and identify the visible link.\n"
            "3. Click the visible link.\n"
            "4. Inspect the destination page.\n"
            "5. Answer in Chinese.\n"
            "Your final answer must include:\n"
            "1. 点击前页面标题\n"
            "2. 点击前主标题\n"
            "3. 被点击的链接文本\n"
            "4. 点击后到达的页面标题或站点名称\n"
            "5. 一句话总结这次跳转结果\n"
            "Keep the final answer short and factual."
        ),
        mcpServers={
            "playwright": {
                "command": "cmd",
                "args": ["/c", "npx", "-y", "@playwright/mcp@latest"],
            }
        },
    )

    try:
        result = await agent(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "请实际打开网页、点击页面里的链接，再读取点击前后的页面结果。"
                            "不要只凭常识回答。"
                        ),
                    }
                ],
                "temperature": 0.1,
            }
        )
        for message in result["messages"]:
            print(message)
    finally:
        await agent._mcp_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
