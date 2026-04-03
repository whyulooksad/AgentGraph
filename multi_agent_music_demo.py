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

    music_agent = Agent(
        name="music_agent",
        description="负责打开 QQ 音乐网页版、搜索歌曲并尝试播放。",
        model="qwen-plus",
        instructions=(
            "You are a browser music operator.\n"
            "You must use Playwright MCP tools to operate the browser.\n"
            "Treat the task as a QQ Music web task, not a desktop native app task.\n"
            "Your workflow must be:\n"
            "1. Open the QQ Music website or a QQ Music search page.\n"
            "2. Find a way to search for the requested song.\n"
            "3. Try to click the matching song or play button.\n"
            "4. Inspect the page again.\n"
            "5. Answer in Chinese.\n"
            "Do not claim playback succeeded unless tool results support it.\n"
            "If the page blocks playback, requires login, or the song cannot be confirmed, say so clearly.\n"
            "Your final answer must include:\n"
            "1. 你打开的页面\n"
            "2. 你尝试点击的元素\n"
            "3. 当前是否能确认已经播放\n"
            "4. 如果失败，失败原因是什么\n"
            "Keep the answer factual and concise."
        ),
        mcpServers={
            "playwright": {
                "command": "cmd",
                "args": ["/c", "npx", "-y", "@playwright/mcp@latest"],
            }
        },
    )

    router_agent = Agent(
        name="router_agent",
        model="qwen-plus",
        instructions=(
            "You are the entry agent for a multi-agent assistant.\n"
            "Your job is to route the user request to the correct subagent.\n"
            "If the user wants to open music, search a song, or play a song, you must call music_agent.\n"
            "Do not answer the task yourself if it belongs to music_agent.\n"
            "After handing off, let the delegated agent finish the task."
        ),
        nodes={music_agent},
    )

    try:
        result = await router_agent(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "帮我打开 QQ 音乐网页版，搜索并尝试播放《见字如面》这首歌。",
                    }
                ],
                "temperature": 0.1,
            }
        )
        for index, message in enumerate(result["messages"], start=1):
            print(f"[{index}] {message}")
    finally:
        await router_agent._mcp_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
