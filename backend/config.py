from __future__ import annotations

"""Story2Proposal 应用层的路径与配置入口。

这个文件集中管理静态路径和基础配置。
"""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# 定义应用层使用的基础目录。
REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = REPO_ROOT / "backend"
PROMPTS_DIR = PACKAGE_ROOT / "prompts"
DATA_DIR = PACKAGE_ROOT / "data"
STORIES_DIR = DATA_DIR / "stories"
OUTPUTS_DIR = DATA_DIR / "outputs"

# 统一加载 `.env`。
load_dotenv(REPO_ROOT / ".env")

DEFAULT_MODEL = os.getenv("STORY2PROPOSAL_MODEL", "qwen-plus")


def load_mcp_server(name: str) -> dict[str, Any] | None:
    """从 `.mcp.json` 中读取指定 MCP server 配置。"""
    mcp_path = REPO_ROOT / ".mcp.json"
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
