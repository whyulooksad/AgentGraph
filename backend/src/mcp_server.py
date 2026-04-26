"""把 Agent graph暴露成 MCP server"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .agent import Agent
from .types import CompletionCreateParams


def create_mcp_server(agent: Agent) -> Any:
    """返回一个把 Agent graph 暴露成 MCP tool 的 server"""
    server = FastMCP(name=agent.name, instructions=agent.instructions)

    def wrapper(target_agent: Agent):
        async def call_agent(
            messages: list[dict[str, Any]],
            context: dict[str, Any] | None = None,
            auto_execute_tools: bool = True,
            max_tokens: int | None = None,
        ) -> dict[str, Any]:
            del auto_execute_tools
            state: CompletionCreateParams = {"messages": messages}
            if max_tokens is not None:
                state["max_tokens"] = max_tokens
            result = await target_agent(state, context=context)
            return {"messages": result, "context": context}

        return call_agent

    for subagent in agent.agents.values():
        if isinstance(subagent, Agent):
            server.tool(name=subagent.name, description=subagent.description)(
                wrapper(subagent)
            )

    return server
