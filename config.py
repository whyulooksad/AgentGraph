from __future__ import annotations

"""Story2Proposal 应用层的路径与静态配置入口。"""

import os
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PACKAGE_ROOT = Path(__file__).resolve().parent
PROMPTS_DIR = PACKAGE_ROOT / "prompts"
DATA_DIR = PACKAGE_ROOT / "data"
STORIES_DIR = DATA_DIR / "stories"
OUTPUTS_DIR = DATA_DIR / "outputs"

# 统一在配置层加载 `.env`，避免模型名散落在不同入口里各自写死。
load_dotenv(PACKAGE_ROOT / ".env")

DEFAULT_MODEL = os.getenv("STORY2PROPOSAL_MODEL", "qwen-plus")


def load_mcp_server(name: str) -> dict[str, Any] | None:
    """从仓库根目录的 `.mcp.json` 读取某个 MCP server 配置。"""
    mcp_path = PACKAGE_ROOT / ".mcp.json"
    if not mcp_path.exists():
        return None
    payload = json.loads(mcp_path.read_text(encoding="utf-8"))
    servers = payload.get("mcpServers") or {}
    config = servers.get(name)
    return config if isinstance(config, dict) else None


def load_prompt(name: str) -> str:
    """按文件名读取一个 prompt 模板。"""
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8").strip()
