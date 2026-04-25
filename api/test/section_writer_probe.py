from __future__ import annotations

"""Standalone section_writer probe endpoint under api/test."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import DEFAULT_MODEL, load_prompt, load_mcp_server
from domain import build_initial_context, persist_run_state, refresh_prompt_views, save_section_draft
from domain.validation import aggregate_feedback
from llm_io import parse_model
from schemas import (
    ManuscriptContract,
    ResearchStory,
    SectionContract,
    SectionDraft,
    StyleGuide,
    VisualArtifact,
)
from src import Agent

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


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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


def _build_probe_diagnostics(
    payload: SectionWriterProbeRequest,
    draft: SectionDraft,
    contract: ManuscriptContract,
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    section = payload.section.model_dump(mode="json")
    draft_payload = draft.model_dump(mode="json")
    aggregated = aggregate_feedback(section, draft_payload, [])

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
    diagnostics = _build_probe_diagnostics(payload, draft, contract, result["messages"])
    _write_json(diagnostics_path, diagnostics)

    return SectionWriterProbeResponse(
        outputDir=str(output_dir),
        draft=draft,
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


@router.post("/section-writer/probe", response_model=SectionWriterProbeResponse)
def section_writer_probe(payload: SectionWriterProbeRequest) -> SectionWriterProbeResponse:
    try:
        return asyncio.run(_run_probe(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
