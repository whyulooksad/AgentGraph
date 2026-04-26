# Story2Proposal Draw.io MCP

`servers/drawio_mcp` is the repository-local draw.io MCP server used by Story2Proposal.

It is maintained as a first-class internal component, not as an ad hoc vendored tarball and not as an `npx`-resolved runtime dependency. The upstream project was cloned from `Sujimoshi/drawio-mcp`, then adapted for this repository's runtime model and Node 22 environment.

## Role In This Repository

This server is responsible for one thing only: creating and editing `.drawio.svg` diagram assets through MCP tools.

It does not own Story2Proposal workflow state, run persistence, contract updates, or hook execution. Those remain in the separate `s2p_workflow` MCP server implemented in [servers/workflow.py](E:/Work/Story2Proposal/servers/workflow.py).

The intended split is:

- `s2p_workflow`: Story2Proposal-specific workflow hooks and state transitions
- `drawio`: diagram generation and mutation against draw.io-compatible SVG files

Keeping them separate avoids coupling diagram tooling to workflow orchestration and makes each server independently maintainable.

## Why This Fork Exists

The upstream package was originally consumed through `npx drawio-mcp`, which is a weak fit for this repository:

- runtime behavior depends on the external npm registry at startup time
- upgrades are implicit instead of reviewable
- Node 22 startup is incompatible with the upstream global DOM bootstrap
- local debugging and patching are awkward

This local fork fixes those problems.

## Local Changes From Upstream

The current fork intentionally diverges from upstream in a few areas:

- It is built and launched locally from this repo, not fetched via `npx`.
- It targets `Node >= 22`.
- Its jsdom bootstrap was rewritten to avoid direct assignment to read-only globals such as `globalThis.navigator` under Node 22.
- Its logger was rewritten to use ESM-safe path resolution instead of `__dirname`.
- Its MCP configuration is expected to be wired through the repository root [`.mcp.json`](E:/Work/Story2Proposal/.mcp.json).

These are not temporary compatibility shims. They are part of the supported local runtime contract for this project.

## Directory Layout

```text
servers/drawio_mcp/
+-- src/
|   +-- index.ts               # MCP server entry
|   +-- Graph.ts               # Graph model and layout behavior
|   +-- GraphFileManager.ts    # .drawio.svg load/save logic
|   +-- Logger.ts              # Local file logger
|   +-- mcp/
|   |   +-- McpServer.ts
|   |   +-- NewDiagramTool.ts
|   |   +-- AddNodeTool.ts
|   |   +-- LinkNodesTools.ts
|   |   +-- EditNodeTool.ts
|   |   +-- RemoveNodesTool.ts
|   |   \-- GetDiagramInfoTool.ts
|   \-- mxgraph/
|       +-- index.ts
|       +-- jsdom.ts
|       \-- installGlobals.ts  # Node 22-safe DOM global installation
+-- package.json
+-- tsconfig.json
\-- README.md
```

## Requirements

- Node.js `>= 22`
- npm

This component is intentionally independent from the Python runtime used by the main Story2Proposal backend.

## Install

From the repository root:

```powershell
cd E:\Work\Story2Proposal\servers\drawio_mcp
npm install
```

## Build

```powershell
cd E:\Work\Story2Proposal\servers\drawio_mcp
npm run build
```

Build output is emitted to `dist/`.

## Start Modes

### 1. Production-like Local Start

Use this when the server should behave the same way as it does under MCP client launch:

```powershell
cd E:\Work\Story2Proposal\servers\drawio_mcp
npm run build
npm start
```

This runs:

```text
node dist/index.js
```

### 2. Development Start

Use this when editing the TypeScript source directly:

```powershell
cd E:\Work\Story2Proposal\servers\drawio_mcp
npm run dev
```

This runs the server through `tsx` against `src/index.ts`.

## MCP Wiring

The repository root [`.mcp.json`](E:/Work/Story2Proposal/.mcp.json) is the source of truth for MCP client registration.

Current wiring is conceptually:

```json
{
  "mcpServers": {
    "s2p_workflow": {
      "command": "E:\\Work\\Story2Proposal\\.venv\\Scripts\\python.exe",
      "args": ["-m", "servers.workflow"]
    },
    "drawio": {
      "command": "node",
      "args": ["E:\\Work\\Story2Proposal\\servers\\drawio_mcp\\dist\\index.js"]
    }
  }
}
```

Important:

- `drawio` assumes `dist/index.js` already exists.
- If you change `src/`, rebuild before starting the MCP client.
- This server should remain a separate MCP entry rather than being merged into `s2p_workflow`.

## Tool Surface

This server currently exposes these MCP tools:

- `new_diagram`
- `add_nodes`
- `link_nodes`
- `edit_nodes`
- `remove_nodes`
- `get_diagram_info`

All tools are stateless with respect to server memory. The diagram file path is always passed explicitly, and the source of truth is the target `.drawio.svg` file on disk.

## File Semantics

Generated files are standard `.drawio.svg` assets with embedded draw.io metadata.

That gives you:

- a normal SVG artifact
- editability in draw.io-compatible tooling
- a file format suitable for versioning in git

Relative paths are resolved from the MCP server process working directory. In this repository, prefer absolute paths or repo-root-relative conventions that are unambiguous in automation.

## Operational Guidance

- Keep diagram generation concerns here, not in `servers/workflow.py`.
- If Story2Proposal needs new diagram operations, add them as explicit MCP tools rather than leaking draw.io internals upward.
- If Node compatibility changes again in future releases, fix the environment bootstrap in `src/mxgraph/` first.
- Treat upstream sync as a code review exercise, not a blind overwrite.

## Verification Workflow

After changing this component, the minimum expected verification is:

```powershell
cd E:\Work\Story2Proposal\servers\drawio_mcp
npm run build
node dist/index.js
```

And, when behavior changes touch file generation, also exercise at least one real tool path such as:

- create a new diagram
- add one or more nodes
- inspect the generated `.drawio.svg`

## Maintenance Notes

- Upstream source reference: `https://github.com/Sujimoshi/drawio-mcp`
- This repository owns the forked behavior needed for Story2Proposal.
- Prefer small, reviewable upgrades from upstream instead of periodic wholesale replacement.

## Non-Goals

This component is not intended to:

- manage Story2Proposal run state
- persist paper workflow artifacts
- replace the Python workflow hook server
- hide upstream/runtime incompatibilities behind startup hacks

If a change pushes in one of those directions, it likely belongs somewhere else.
