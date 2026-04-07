# Agent Framework Context

This project implements a graph-driven agent runtime. The runtime centers on `Agent` nodes, explicit `Edge` transitions, MCP-backed `Tool` nodes, optional skill gating, and agent-scoped memory integration.

## Core Model

- `Agent` is both a graph node and a runnable local graph root.
- `Node` is the shared executable abstraction used by agents and tool nodes.
- `Edge` defines control-flow transitions between nodes.
- `Tool` wraps one MCP tool call as a graph node bound to an MCP client session.
- Execution is graph-driven: one LLM turn can create agents, edges, tool nodes, and follow-up execution paths.

## Main Components

- `agent.py`
  Core runtime. It prepares prompts, exposes built-in graph tools, calls the LLM, translates tool calls into graph mutations, executes downstream nodes, runs hooks, supports non-streaming and streaming execution, and manages runtime cleanup.

- `nodes.py`
  Defines the abstract `Node` type and the MCP-backed `Tool` node. `Tool.__call__` validates arguments against the MCP tool schema before dispatch.

- `edge.py`
  Defines graph edges. `source` can be a single node name or a tuple of node names. Tuple sources behave like a join: all listed sources must have completed, and at least one of them must be newly completed in the current step.

- `mcp_manager.py`
  Connects to stdio or SSE MCP servers, loads remote tool schemas, exposes them as OpenAI function tools named `mcp__<server>__<tool>`, creates runtime `Tool` nodes, executes tool calls, and converts MCP results into OpenAI-compatible tool messages.

- `mcp_server.py`
  Exposes an agent graph as an MCP server via FastMCP. Each reachable agent is exported as an MCP tool.

- `_settings.py`
  Loads settings from `.env`, environment variables, `~/.claude.json`, project `.mcp.json`, and `agents_md` paths. Root `AGENTS.md` content is injected into the system prompt as additional long-term project context.

- `hook.py`
  Defines lifecycle hook configuration. Hook values are MCP tool names, not Python callbacks.

- `memory.py`
  Defines the `MemoryProvider` interface plus lightweight query and record models. Memory is optional and agent-scoped.

- `skill.py`
  Defines filesystem-backed skills, per-agent skill catalogs, tool visibility policy, and inheritance rules for dynamically created child agents.

## Execution Flow

1. An `Agent` receives `messages` and optional `context`.
2. The runtime loads visible MCP servers from global settings plus `agent.mcp_servers`.
3. Optional memory context is loaded through the configured `MemoryProvider`.
4. The system prompt is assembled from:
   `agent.instructions`
   active skill catalog guidance, if a skill catalog is attached but no skill is active
   active skill instructions, if a skill has been activated
   root `AGENTS.md` content from settings
5. The runtime exposes tools to the model:
   visible MCP tools
   callable child agents and the current agent
   built-in `create_agent`
   built-in `create_edge`
   built-in `activate_skill` when a skill catalog is attached
6. The LLM returns assistant content and optionally `tool_calls`.
7. Tool calls are translated into graph mutations or synthetic tool results:
   `create_agent` creates a child `Agent` and shares runtime state with it
   `create_edge` adds an `Edge`
   calling an agent by name creates a handoff edge from the current agent
   MCP tool calls create runtime `Tool` nodes plus forward and return edges
   `activate_skill` activates one skill and adds a self-edge so the agent can continue with the new tool scope
   blocked MCP tool calls produce a synthetic tool message instead of executing
8. The runtime executes all triggered downstream targets. In non-streaming mode, ready targets for the same step run concurrently with `asyncio.TaskGroup`.
9. `on_end` hooks run, memory is saved, and temporary runtime tool nodes and their edges are cleaned up.

## Edge Resolution

- An edge target may be:
  a node name in the current agent graph
  an MCP tool name that returns the next node name or list of node names
  a CEL expression evaluated against `context`
- Conditional edge resolution must produce a string node name or a list of string node names.

## Hooks

- Implemented hook stages: `on_start`, `on_end`, `on_handoff`, `on_tool_start`, `on_tool_end`, `on_llm_start`, `on_llm_end`, `on_chunk`.
- Hook tools are regular MCP tools. The runtime passes only fields declared in the hook tool input schema, selected from values such as `messages`, `context`, `agent`, `to_agent`, `tool`, `available_tools`, `chunk`, and `completion`.
- Hook tools must return `structuredContent`; the returned fields are merged into runtime `context`.

## Skills

- Skills are optional and filesystem-backed.
- `Agent.with_skill_loader(...)` attaches one agent-scoped skill catalog.
- Before a skill is activated, the model is instructed to choose a skill first and MCP tools are hidden.
- After activation, MCP tool visibility is restricted by `toolNames` or `visibleMcpServers`.
- Child agents inherit skill boundaries through `Skill.for_child()`, not the full parent skill instructions.

## Memory

- `Agent.with_memory(...)` attaches a `MemoryProvider`.
- `load_context(...)` runs before execution and can merge additional values into `context`.
- `save(...)` runs after execution completes.
- `search(...)` is defined on the provider interface for explicit retrieval workflows, but the base runtime does not call it automatically.

## Streaming

- `Agent.stream(...)` is implemented.
- Streaming emits structured events such as `agent_start`, `llm_start`, `chunk`, `token`, `completion_message`, `message`, `tool_result`, `agent_end`, and final `done`.
- In streaming mode, downstream graph execution is processed sequentially rather than with a task group.

## Important Behaviors

- Agent names must be unique across the graph; duplicates raise an error during graph collection.
- MCP tools are exposed with OpenAI function-tool shape and namespaced as `mcp__<server>__<tool>`.
- Hook tools are excluded from the normal visible tool list so the model cannot call them directly unless separately exposed.
- User messages named `approval` are filtered out before sending messages to the LLM.
- Fields like `parsed` and `reasoning_content` are stripped from outbound chat messages before LLM calls.
- The default OpenAI client uses `OPENAI_API_KEY` and `OPENAI_BASE_URL` from settings unless an agent-specific `client` is provided.
- Settings merge MCP server config recursively on `mcpServers`; later sources override earlier ones.
- `settings.agents_md` can be one path or multiple paths, and each existing file is appended to the system prompt as fenced Markdown.
- Temporary MCP tool nodes created for one run are removed after execution, along with their related edges and visited-state entries.

## Guidance For Agents

- Describe this framework as a graph runtime with dynamic node and edge creation, not as a simple sequential tool loop.

- Mention skills and memory only when they are actually configured; they are optional capabilities.

- Do not claim arbitrary streaming semantics beyond the event flow implemented in `Agent.stream`.

- When explaining tool visibility, note that skills can hide MCP tools until `activate_skill` is called.

  
