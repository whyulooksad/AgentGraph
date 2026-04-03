"""MCP client"""

from __future__ import annotations

import mimetypes
import os
import re
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, assert_never

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.shared.session import ProgressFnT
from mcp.types import (
    BlobResourceContents,
    CallToolResult,
    ContentBlock,
    EmbeddedResource,
    ImageContent,
    ResourceContents,
    TextResourceContents,
)
from mcp.types import Tool as MCPTool
from pygments.lexers import get_lexer_for_filename, get_lexer_for_mimetype
from pygments.util import ClassNotFound

from .nodes import Tool
from .types import MCPServer

mimetypes.add_type("text/markdown", ".md")


@dataclass
class MCPManager:
    """MCP 工具注册表"""

    exit_stack: AsyncExitStack = field(default_factory=AsyncExitStack)
    mcp_clients: dict[str, ClientSession] = field(default_factory=dict)
    _tools: dict[str, list[MCPTool]] = field(default_factory=dict)

    @property
    def tools(self) -> list[dict[str, Any]]:
        """返回全部 MCP tools"""
        tools: list[dict[str, Any]] = []
        for server, server_tools in self._tools.items():
            for tool in server_tools:
                payload = {
                    "type": "function",
                    "function": {
                        "name": f"mcp__{server}__{tool.name}",
                        "parameters": tool.inputSchema,
                    },
                }
                if tool.description:
                    payload["function"]["description"] = tool.description
                tools.append(payload)
        return tools

    def _parse_name(self, name: str) -> tuple[str, MCPTool]:
        if (mo := re.match(r"mcp__(?P<server>[^/]+)__(?P<name>[^/]+)", name)) is None:
            raise ValueError("Invalid tool name, expected mcp__<server>__<tool>")
        server_name, tool_name = mo.group("server"), mo.group("name")
        if server_name not in self.mcp_clients:
            raise KeyError(f"Server {server_name} not found")
        for tool in self._tools[server_name]:
            if tool.name == tool_name:
                return server_name, tool
        raise KeyError(f"Tool {tool_name} not found")

    def get_tool(self, name: str) -> MCPTool:
        """按 name 获取 MCP tool"""
        _, tool = self._parse_name(name)
        return tool

    def make_tool_node(
        self,
        name: str,
        tool_call_id: str,
        arguments: dict[str, Any] | None = None,
    ) -> Tool:
        """创建一个绑定到当前 manager 的 MCP Tool 节点"""
        server_name, tool = self._parse_name(name)
        payload = tool.model_dump(mode="python") if hasattr(tool, "model_dump") else dict(tool)
        payload["name"] = f"{name}__call__{self._sanitize_call_id(tool_call_id)}"
        payload["tool_name"] = name
        payload["tool_call_id"] = tool_call_id
        payload["tool_arguments"] = arguments
        payload.setdefault("description", f"{tool.description or ''} (from {server_name})".strip())
        payload["session"] = self.mcp_clients[server_name]
        return Tool.model_validate(payload)

    @staticmethod
    def _sanitize_call_id(tool_call_id: str) -> str:
        """把 tool call id 转成适合放进节点名的安全字符串"""
        safe = re.sub(r"[^A-Za-z0-9_]", "_", tool_call_id)
        return safe or "call"

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        read_timeout_seconds: timedelta | None = None,
        progress_callback: ProgressFnT | None = None,
        *,
        meta: dict[str, Any] | None = None,
    ):
        """调用 MCP tool"""
        server_name, tool = self._parse_name(name)
        return await self.mcp_clients[server_name].call_tool(
            tool.name,
            arguments,
            read_timeout_seconds,
            progress_callback,
            meta=meta,
        )

    async def add_server(self, name: str, server_params: MCPServer):
        """添加一个 MCP server"""
        if name in self.mcp_clients:
            return
        read_stream, write_stream = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
            if isinstance(server_params, StdioServerParameters)
            else sse_client(server_params.url, server_params.headers)
        )
        client = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        await client.initialize()
        self.mcp_clients[name] = client
        self._tools[name] = (await client.list_tools()).tools

    async def close(self):
        """关闭全部 MCP client"""
        try:
            await self.exit_stack.aclose()
        except RuntimeError as exc:
            if "cancel scope" not in str(exc):
                raise
        self.mcp_clients = {}
        self._tools = {}


def _image_to_md(content: ImageContent) -> str:
    alt = (content.meta or {}).get("alt", "")
    return f"![{alt}](data:{content.mimeType};base64,{content.data})"


def _resource_to_md(resource: EmbeddedResource) -> str:
    def get_filename(content: ResourceContents) -> str:
        if content.uri.path is not None:
            return os.path.basename(content.uri.path)
        if content.uri.host is not None:
            return content.uri.host
        raise ValueError("Cannot determine filename for resource.")

    def get_lang(content: ResourceContents) -> str:
        if content.mimeType is None:
            try:
                lexer = get_lexer_for_filename(get_filename(content))
            except ClassNotFound:
                lexer = None
        else:
            try:
                lexer = get_lexer_for_mimetype(content.mimeType)
            except ClassNotFound:
                lexer = None
        return lexer.aliases[0] if lexer else "text"

    match resource.resource:
        case TextResourceContents() as content:
            if content.mimeType in ("text/markdown", "text/plain"):
                return f"\n<!-- begin {content.uri} -->\n{content.text}\n<!-- end {content.uri} -->\n"
            lang = get_lang(content)
            return f'\n```{lang} title="{content.uri}"\n{content.text}\n```\n'
        case BlobResourceContents() as content:
            return (
                "<embed"
                f' type="{content.mimeType or "application/octet-stream"}"'
                f' src="data:{content.mimeType or ""};base64,{content.blob}"'
                f' title="{content.uri}"'
                " />"
            )
        case _ as unreachable:
            assert_never(unreachable)


def result_to_content(result: CallToolResult) -> list[dict[str, str]]:
    """把 MCP tool 结果转换成文本片段"""

    def to_text(block: ContentBlock) -> str:
        match block.type:
            case "text":
                text = block.text
            case "image":
                text = _image_to_md(block)
            case "resource":
                text = _resource_to_md(block)
            case "audio":
                text = f'<audio src="data:{block.mimeType};base64,{block.data}" />'
            case "resource_link":
                text = f"[{block.name}]({block.uri})"
            case _ as unreachable:
                assert_never(unreachable)
        return text

    return [{"text": to_text(block), "type": "text"} for block in result.content]


def result_to_message(tool_call_id: str, result: CallToolResult | BaseException) -> dict[str, Any]:
    """把 MCP tool 结果转换成 OpenAI 兼容 tool message"""
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": "".join(piece["text"] for piece in result_to_content(result))
        if not isinstance(result, BaseException)
        else str(result),
    }
