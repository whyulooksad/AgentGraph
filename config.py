from __future__ import annotations

"""Story2Proposal 应用层的路径与静态资源入口。"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROMPTS_DIR = PACKAGE_ROOT / "prompts"
DATA_DIR = PACKAGE_ROOT / "data"
STORIES_DIR = DATA_DIR / "stories"
OUTPUTS_DIR = DATA_DIR / "outputs"


def load_prompt(name: str) -> str:
    """按文件名读取一个 prompt 模板。"""
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8").strip()
