# Agent Framework Context

This project implements a lightweight graph-driven agent framework under `src/`.

## Core Model

- `Agent` is both an executable node and the entry point of a local execution graph.
- `Edge` defines control-flow transitions between nodes.
- `Tool` represents MCP tool calls as graph nodes.
- The runtime is graph-driven rather than a simple sequential tool loop.

## Main Components

- `src/agent.py`
  The core runtime. It prepares prompts, calls the LLM, converts tool calls into graph nodes and edges, executes downstream nodes, and manages hooks.

- `src/nodes.py`
  Defines the shared `Node` abstraction and the `Tool` node used for MCP tool execution.

- `src/edge.py`
  Defines graph edges. An edge can be triggered by a single source or by multiple sources.

- `src/mcp_manager.py`
  Connects to MCP servers, loads MCP tools, converts them into OpenAI function tools, and executes MCP tool calls.

- `src/mcp_server.py`
  Exposes the agent graph as MCP tools.

- `src/_settings.py`
  Loads framework settings, including `.env`, `.mcp.json`, `.claude.json`, and this `AGENTS.md`.

- `src/hook.py`
  Defines lifecycle hook configuration. Hook values are MCP tool names, not Python callbacks.

## Execution Flow

1. An `Agent` receives input messages and optional context.
2. The runtime loads MCP servers from settings and agent-local config.
3. The runtime builds the system prompt from `instructions` plus `AGENTS.md`.
4. The LLM returns either plain content or `tool_calls`.
5. Tool calls are translated into:
   - dynamic agent creation via `create_agent`
   - dynamic edge creation via `create_edge`
   - agent-to-agent handoff edges
   - MCP tool nodes and return edges
6. The graph runtime continues executing triggered downstream nodes until no more targets are available.

## Important Behaviors

- `stream=True` is currently not supported.
- MCP tools are exposed to the model as OpenAI function tools.
- Hook execution depends on MCP tools being available with matching names.
- Agent names must be unique across the graph.
- Root `.env` is used for `OPENAI_API_KEY` and `OPENAI_BASE_URL`.
- Root `AGENTS.md` is automatically appended to the system prompt as long-term project context.

## Guidance For Agents

- When describing this project, rely on the actual framework behavior above instead of generic agent-framework assumptions.
- Do not claim support for features that are not implemented in `src/`.
- If asked how the framework works, explain it in terms of graph execution, MCP integration, and runtime tool-call translation.
- If information is missing from code or this file, say the information is not confirmed.
