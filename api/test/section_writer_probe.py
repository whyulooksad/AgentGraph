from __future__ import annotations

"""Standalone section_writer probe endpoint under api/test."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field, TypeAdapter

from config import DEFAULT_MODEL, OUTPUTS_DIR, load_prompt, load_mcp_server
from domain import build_initial_context, persist_run_state, refresh_prompt_views, save_section_draft
from domain.validation import aggregate_feedback
from domain.visual_artifacts import materialize_visual_artifact, normalize_svg_markup
from llm_io import parse_model
from schemas import (
    ManuscriptContract,
    ResearchStory,
    SectionContract,
    SectionDraft,
    StyleGuide,
    VisualArtifact,
)
from schemas.draft import VisualArtifactMaterialization
from src import Agent, MCPManager, MCPServer
from src.mcp_manager import result_to_content

router = APIRouter(prefix="/api/debug")


class SectionWriterProbeRequest(BaseModel):
    story: ResearchStory
    section: SectionContract
    visuals: list[VisualArtifact] = Field(default_factory=list)
    model: str = DEFAULT_MODEL
    mode: Literal["compose", "repair"] = "compose"
    plan: dict[str, Any] = Field(default_factory=dict)


class SectionWriterProbeResponse(BaseModel):
    outputDir: str
    draft: SectionDraft
    contract: ManuscriptContract
    rawOutput: str
    diagnostics: dict[str, Any]
    files: dict[str, str]


class DrawioNodeSpec(BaseModel):
    id: str
    title: str
    kind: str
    x: float
    y: float
    width: float | None = None
    height: float | None = None


class DrawioEdgeSpec(BaseModel):
    from_id: str = Field(alias="from")
    to_id: str = Field(alias="to")
    title: str | None = None
    dashed: bool = False
    reverse: bool = False
    undirected: bool = False


class DrawioProbeRequest(BaseModel):
    diagram_name: str = "system_overview"
    output_subdir: str = "drawio_probe"
    nodes: list[DrawioNodeSpec] = Field(
        default_factory=lambda: [
            DrawioNodeSpec(id="story", title="Research Story", kind="Rectangle", x=40, y=120, width=140, height=60),
            DrawioNodeSpec(id="writer", title="Section Writer", kind="RoundedRectangle", x=260, y=120, width=160, height=70),
            DrawioNodeSpec(id="drawio", title="draw.io MCP", kind="Cloud", x=520, y=120, width=150, height=80),
        ]
    )
    edges: list[DrawioEdgeSpec] = Field(
        default_factory=lambda: [
            DrawioEdgeSpec(**{"from": "story", "to": "writer", "title": "contract context"}),
            DrawioEdgeSpec(**{"from": "writer", "to": "drawio", "title": "materialize visual", "dashed": True}),
        ]
    )


class DrawioProbeResponse(BaseModel):
    outputDir: str
    diagramPath: str
    renderedDiagramPath: str
    availableTools: list[str]
    invokedTools: list[dict[str, Any]]
    fileExists: bool
    fileSize: int | None = None
    diagramPreview: str
    fileUrl: str
    previewUrl: str
    files: dict[str, str]


def _build_probe_contract(payload: SectionWriterProbeRequest, output_dir: Path) -> ManuscriptContract:
    language = payload.story.metadata.get("writing_language")
    output_language = language if language in {"en", "zh"} else "en"
    contract = ManuscriptContract(
        contract_id=f"probe_{output_dir.name}",
        paper_title=payload.story.title_hint or payload.story.topic,
        style_guide=StyleGuide(output_language=output_language),
        sections=[payload.section],
        visuals=payload.visuals,
    )
    contract.global_status.state = "initialized"
    contract.global_status.current_section_id = payload.section.section_id
    contract.global_status.pending_sections = [payload.section.section_id]
    contract.global_status.completed_sections = []
    return contract


def _latest_assistant_message(messages: list[dict[str, object]]) -> str:
    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue
        content = message.get("content")
        if isinstance(content, str):
            return content
    raise ValueError("Section writer did not return an assistant message.")


def _build_section_writer_agent(model: str) -> Agent:
    drawio_config = load_mcp_server("drawio")
    return Agent(
        name="section_writer",
        model=model,
        instructions=load_prompt("section_writer.md"),
        mcpServers=({"drawio": drawio_config} if drawio_config is not None else {}),
    )


def _required_mcp_server(name: str) -> MCPServer:
    config = load_mcp_server(name)
    if config is None:
        raise RuntimeError(f"Missing MCP server config {name!r} in .mcp.json")
    return TypeAdapter(MCPServer).validate_python(config)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _tool_result_payload(result: Any) -> dict[str, Any]:
    return {
        "structuredContent": result.structuredContent,
        "content": result_to_content(result),
        "isError": getattr(result, "isError", False),
    }


def _extract_invoked_tool_names(messages: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for message in messages:
        tool_calls = message.get("tool_calls")
        if not isinstance(tool_calls, list):
            continue
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            function = tool_call.get("function")
            if isinstance(function, dict):
                name = function.get("name")
                if isinstance(name, str) and name:
                    names.append(name)
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return ordered


def _resolve_outputs_file(path: str) -> Path:
    requested = Path(path)
    resolved = requested.resolve() if requested.is_absolute() else (OUTPUTS_DIR / requested).resolve()
    outputs_root = OUTPUTS_DIR.resolve()
    try:
        resolved.relative_to(outputs_root)
    except ValueError as exc:
        raise RuntimeError("Requested file is outside data/outputs.") from exc
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(str(resolved))
    return resolved


def _outputs_relative_path(path: Path) -> str:
    return path.resolve().relative_to(OUTPUTS_DIR.resolve()).as_posix()


def _build_probe_diagnostics(
    payload: SectionWriterProbeRequest,
    draft: SectionDraft,
    contract: ManuscriptContract,
    messages: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    section = payload.section.model_dump(mode="json")
    draft_payload = draft.model_dump(mode="json")
    aggregated = aggregate_feedback(section, draft_payload, [], output_dir=output_dir)

    required_claim_ids = set(payload.section.required_claim_ids or payload.section.required_claims)
    covered_claim_ids = set(draft.covered_claim_ids)
    required_visual_ids = set(payload.section.required_visual_ids)
    referenced_visual_ids = set(draft.referenced_visual_ids)
    required_citation_ids = set(payload.section.required_citation_ids)
    referenced_citation_ids = set(draft.referenced_citation_ids)
    materialized_visual_ids = {artifact.artifact_id for artifact in draft.visual_artifacts}
    drawio_artifact_ids = {
        artifact.artifact_id
        for artifact in draft.visual_artifacts
        if artifact.generator.lower() == "drawio"
    }
    invoked_tool_names = _extract_invoked_tool_names(messages)

    return {
        "status": aggregated["status"],
        "issues": aggregated["issues"],
        "deterministic_checks": aggregated["deterministic_checks"],
        "contract_patches": aggregated["patches"],
        "covered_claim_ids": sorted(covered_claim_ids),
        "missing_required_claim_ids": sorted(required_claim_ids - covered_claim_ids),
        "referenced_visual_ids": sorted(referenced_visual_ids),
        "missing_required_visual_ids": sorted(required_visual_ids - referenced_visual_ids),
        "materialized_visual_ids": sorted(materialized_visual_ids),
        "unmaterialized_required_visual_ids": sorted(required_visual_ids - materialized_visual_ids),
        "referenced_citation_ids": sorted(referenced_citation_ids),
        "missing_required_citation_ids": sorted(required_citation_ids - referenced_citation_ids),
        "unresolved_items": list(draft.unresolved_items),
        "invoked_tool_names": invoked_tool_names,
        "used_drawio_tool": any(name.startswith("mcp__drawio__") for name in invoked_tool_names),
        "drawio_artifact_ids": sorted(drawio_artifact_ids),
        "contract_visual_status": {
            artifact.artifact_id: {
                "materialization_status": artifact.materialization_status,
                "render_status": artifact.render_status,
                "generator": artifact.generator,
                "source_path": artifact.source_path,
                "rendered_path": artifact.rendered_path,
            }
            for artifact in contract.visuals
        },
    }


async def _run_probe(payload: SectionWriterProbeRequest) -> SectionWriterProbeResponse:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("data") / "outputs" / f"{payload.story.story_id}_section_writer_probe_{timestamp}"
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "rendered").mkdir(exist_ok=True)
    (output_dir / "drafts").mkdir(exist_ok=True)
    (output_dir / "reviews").mkdir(exist_ok=True)
    (output_dir / "logs").mkdir(exist_ok=True)

    context = build_initial_context(payload.story, output_dir)
    contract = _build_probe_contract(payload, output_dir)
    context["contract"] = contract.model_dump(mode="json")
    context["runtime"]["current_section_id"] = payload.section.section_id
    context["runtime"]["pending_sections"] = [payload.section.section_id]
    context["runtime"]["completed_sections"] = []
    context["runtime"]["rewrite_count"] = {payload.section.section_id: 0}
    context["runtime"]["current_draft_version"] = 0
    context["runtime"]["section_writer_mode"] = payload.mode
    context["runtime"]["section_writer_plan"] = payload.plan
    refresh_prompt_views(context)
    persist_run_state(context)

    agent = _build_section_writer_agent(payload.model)
    try:
        result = await agent(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Write the current section and return JSON only.",
                    }
                ],
                "temperature": 0.2,
            },
            context=context,
        )
    finally:
        await agent._mcp_manager.close()

    raw_output = _latest_assistant_message(result["messages"])
    draft = parse_model(raw_output, SectionDraft)
    save_section_draft(context, draft)
    persist_run_state(context)
    contract = ManuscriptContract.model_validate(context["contract"])

    logs_dir = output_dir / "logs"
    draft_version = context["runtime"]["current_draft_version"]
    raw_output_path = logs_dir / "section_writer_raw_output.json"
    messages_path = logs_dir / "section_writer_messages.json"
    diagnostics_path = logs_dir / "section_writer_probe_diagnostics.json"
    draft_path = output_dir / "drafts" / f"{payload.section.section_id}_v{draft_version}.md"
    run_state_path = logs_dir / "run_state.json"

    _write_json(raw_output_path, {"raw_output": raw_output})
    _write_json(messages_path, result["messages"])
    normalized_draft = SectionDraft.model_validate(context["drafts"][payload.section.section_id])
    diagnostics = _build_probe_diagnostics(payload, normalized_draft, contract, result["messages"], output_dir)
    _write_json(diagnostics_path, diagnostics)

    return SectionWriterProbeResponse(
        outputDir=str(output_dir),
        draft=normalized_draft,
        contract=contract,
        rawOutput=raw_output,
        diagnostics=diagnostics,
        files={
            "draft_path": str(draft_path),
            "raw_output_path": str(raw_output_path),
            "messages_path": str(messages_path),
            "diagnostics_path": str(diagnostics_path),
            "run_state_path": str(run_state_path),
        },
    )


async def _run_drawio_probe(payload: DrawioProbeRequest) -> DrawioProbeResponse:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = (Path("data") / "outputs" / f"{payload.output_subdir}_{timestamp}").resolve()
    logs_dir = output_dir / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(exist_ok=True)

    diagram_path = output_dir / f"{payload.diagram_name}.drawio.svg"
    manager = MCPManager()
    try:
        await manager.add_server("drawio", _required_mcp_server("drawio"))
        available_tools = sorted(
            tool["function"]["name"]
            for tool in manager.tools
            if tool.get("type") == "function"
        )

        invoked_tools: list[dict[str, Any]] = []

        new_diagram_result = await manager.call_tool(
            "mcp__drawio__new_diagram",
            {"file_path": str(diagram_path)},
        )
        invoked_tools.append(
            {
                "name": "mcp__drawio__new_diagram",
                "arguments": {"file_path": str(diagram_path)},
                "result": _tool_result_payload(new_diagram_result),
            }
        )

        add_nodes_args = {
            "file_path": str(diagram_path),
            "nodes": [node.model_dump(mode="json", exclude_none=True) for node in payload.nodes],
        }
        add_nodes_result = await manager.call_tool("mcp__drawio__add_nodes", add_nodes_args)
        invoked_tools.append(
            {
                "name": "mcp__drawio__add_nodes",
                "arguments": add_nodes_args,
                "result": _tool_result_payload(add_nodes_result),
            }
        )

        if payload.edges:
            link_edges_args = {
                "file_path": str(diagram_path),
                "edges": [
                    {
                        "from": edge.from_id,
                        "to": edge.to_id,
                        "title": edge.title,
                        "dashed": edge.dashed,
                        "reverse": edge.reverse,
                        "undirected": edge.undirected,
                    }
                    for edge in payload.edges
                ],
            }
            link_edges_result = await manager.call_tool("mcp__drawio__link_nodes", link_edges_args)
            invoked_tools.append(
                {
                    "name": "mcp__drawio__link_nodes",
                    "arguments": link_edges_args,
                    "result": _tool_result_payload(link_edges_result),
                }
            )

        info_result = await manager.call_tool(
            "mcp__drawio__get_diagram_info",
            {"file_path": str(diagram_path)},
        )
        info_payload = _tool_result_payload(info_result)
        invoked_tools.append(
            {
                "name": "mcp__drawio__get_diagram_info",
                "arguments": {"file_path": str(diagram_path)},
                "result": info_payload,
            }
        )

        trace_path = logs_dir / "drawio_probe_trace.json"
        _write_json(
            trace_path,
            {
                "available_tools": available_tools,
                "invoked_tools": invoked_tools,
                "diagram_path": str(diagram_path),
            },
        )

        rendered_artifact = materialize_visual_artifact(
            output_dir,
            VisualArtifactMaterialization(
                artifact_id=payload.diagram_name,
                generator="drawio",
                source_path=diagram_path.name,
            ),
        )
        rendered_diagram_path = output_dir / (rendered_artifact.rendered_path or diagram_path.name)
        preview = rendered_diagram_path.read_text(encoding="utf-8")[:1200] if rendered_diagram_path.exists() else ""
        relative_diagram_path = _outputs_relative_path(rendered_diagram_path)
        return DrawioProbeResponse(
            outputDir=str(output_dir),
            diagramPath=str(diagram_path),
            renderedDiagramPath=str(rendered_diagram_path),
            availableTools=available_tools,
            invokedTools=invoked_tools,
            fileExists=rendered_diagram_path.exists(),
            fileSize=rendered_diagram_path.stat().st_size if rendered_diagram_path.exists() else None,
            diagramPreview=preview,
            fileUrl=f"/api/debug/drawio/file?path={relative_diagram_path}",
            previewUrl=f"/api/debug/drawio/preview?path={relative_diagram_path}",
            files={
                "diagram_path": str(diagram_path),
                "rendered_diagram_path": str(rendered_diagram_path),
                "trace_path": str(trace_path),
            },
        )
    finally:
        await manager.close()


@router.post("/section-writer/probe", response_model=SectionWriterProbeResponse)
def section_writer_probe(payload: SectionWriterProbeRequest) -> SectionWriterProbeResponse:
    try:
        return asyncio.run(_run_probe(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/drawio/probe", response_model=DrawioProbeResponse)
def drawio_probe(payload: DrawioProbeRequest) -> DrawioProbeResponse:
    try:
        return asyncio.run(_run_drawio_probe(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/drawio/file")
def drawio_probe_file(
    path: str = Query(..., description="Relative path within data/outputs to one generated draw.io artifact."),
) -> FileResponse:
    try:
        resolved = _resolve_outputs_file(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Drawio artifact not found: {path}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FileResponse(resolved, media_type="image/svg+xml")


@router.get("/drawio/preview")
def drawio_probe_preview(
    path: str = Query(..., description="Relative path within data/outputs to one generated draw.io artifact."),
) -> HTMLResponse:
    try:
        resolved = _resolve_outputs_file(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Drawio artifact not found: {path}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    relative_path = _outputs_relative_path(resolved)
    file_url = f"/api/debug/drawio/file?path={relative_path}"
    artifact_name = resolved.name
    svg_markup = _normalize_svg_markup(resolved.read_text(encoding="utf-8"))
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{artifact_name}</title>
    <style>
      :root {{
        color-scheme: light;
        font-family: "Segoe UI", Arial, sans-serif;
        background: #f3f6fb;
        color: #162033;
      }}
      body {{
        margin: 0;
        padding: 24px;
      }}
      .shell {{
        max-width: 1200px;
        margin: 0 auto;
        display: grid;
        gap: 16px;
      }}
      .card {{
        background: #ffffff;
        border: 1px solid #d6deea;
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 14px 30px rgba(22, 32, 51, 0.08);
      }}
      .meta {{
        font-size: 14px;
        color: #5f6f86;
      }}
      .visual {{
        min-height: 70vh;
        overflow: auto;
      }}
      .visual svg {{
        display: block;
        max-width: 100%;
        height: auto;
        margin: 0 auto;
      }}
      .visual-fallback {{
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid #d6deea;
        font: 12px/1.5 Consolas, monospace;
        color: #5f6f86;
        white-space: pre-wrap;
        word-break: break-all;
        max-height: 220px;
        overflow: auto;
      }}
      .visual-shell {{
        min-width: fit-content;
        display: block;
      }}
      a {{
        color: #0f5bd8;
        text-decoration: none;
      }}
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="card">
        <h1 style="margin: 0 0 8px;">draw.io Probe Preview</h1>
        <div class="meta">{artifact_name}</div>
        <div class="meta">source: {relative_path}</div>
        <div class="meta"><a href="{file_url}" target="_blank" rel="noreferrer">Open raw SVG</a></div>
      </section>
      <section class="card visual">
        <div class="visual-shell">
          {svg_markup}
        </div>
        <div class="visual-fallback">{artifact_name}</div>
      </section>
    </main>
  </body>
</html>"""
    return HTMLResponse(content=html)


def create_app() -> FastAPI:
    app = FastAPI(title="Story2Proposal Test API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.test.section_writer_probe:app", host="127.0.0.1", port=8010, reload=False)
