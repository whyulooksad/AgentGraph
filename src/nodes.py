from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import timedelta
from typing import Annotated, Any

import jsonschema
from mcp import ClientSession
from mcp import Tool as MCPToolBase
from mcp.shared.session import ProgressFnT
from mcp.types import CallToolResult
from pydantic import Field, PrivateAttr


class Node[I, O](MCPToolBase, metaclass=ABCMeta):
    """graph runtime 时的基础节点"""

    name: Annotated[str, Field(frozen=True)]

    def __hash__(self) -> int:
        return hash(self.name)

    @abstractmethod
    async def __call__(
        self,
        arguments: I | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> O:
        """执行该节点"""


class Tool(Node[dict[str, Any] | None, CallToolResult]):
    """执行 MCP 工具调用的 graph 节点"""

    name: Annotated[
        str,
        Field(
            pattern=(
                "^mcp__"
                r"([A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*)__"
                r"([A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*)"
            ),
            frozen=True,
        ),
    ]
    tool_name: str | None = None
    tool_call_id: str | None = None
    tool_arguments: dict[str, Any] | None = None

    _session: ClientSession | None = PrivateAttr(default=None)

    def model_post_init(self, __context: Any) -> None:
        extra = getattr(self, "model_extra", None) or {}
        self._session = extra.pop("session", None)

    async def __call__(
        self,
        arguments: dict[str, Any] | None = None,
        read_timeout_seconds: timedelta | None = None,
        progress_callback: ProgressFnT | None = None,
        *,
        meta: dict[str, Any] | None = None,
    ) -> CallToolResult:
        if self._session is None:
            raise RuntimeError(
                f"Client session not found, tool `{self.name}` cannot be executed."
            )
        jsonschema.validate(arguments, self.inputSchema)
        tool_name = self.tool_name or self.name
        return await self._session.call_tool(
            tool_name.split("__", maxsplit=2)[2],
            arguments,
            read_timeout_seconds,
            progress_callback,
            meta=meta,
        )
