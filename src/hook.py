from typing import Literal

from pydantic import BaseModel


class Hook(BaseModel):
    """Agent 生命周期 hook 配置

    每个字段存的都是 MCP tool 名称，而不是 Python 函数引用
    """

    on_start: str | None = None
    on_end: str | None = None
    on_handoff: str | None = None
    on_tool_start: str | None = None
    on_tool_end: str | None = None
    on_llm_start: str | None = None
    on_llm_end: str | None = None
    on_chunk: str | None = None


HookType = Literal[
    "on_start",
    "on_end",
    "on_handoff",
    "on_tool_start",
    "on_tool_end",
    "on_llm_start",
    "on_llm_end",
    "on_chunk",
]
