from __future__ import annotations

"""Story2Proposal agent definitions."""

from src import Agent, Hook

from config import load_mcp_server, load_prompt


def _required_mcp_server_config(name: str) -> dict[str, object]:
    """Return one required MCP server config from repo-local `.mcp.json`."""
    config = load_mcp_server(name)
    if config is None:
        raise RuntimeError(f"Missing MCP server config {name!r} in .mcp.json")
    return config


def drawio_server_config() -> dict[str, object] | None:
    """Return draw.io MCP config from repo-local `.mcp.json`."""
    return load_mcp_server("drawio")


def workflow_server_config() -> dict[str, object]:
    """Return workflow MCP config from repo-local `.mcp.json`."""
    return _required_mcp_server_config("s2p_workflow")


def _make_agent(
    name: str,
    model: str,
    prompt_name: str,
    *,
    on_start: str | None = None,
    on_end: str | None = None,
    mcp_servers: dict[str, object] | None = None,
) -> Agent:
    """Construct one application-layer agent with shared conventions."""
    hooks: list[Hook] = []
    if on_start is not None or on_end is not None:
        hooks.append(Hook(on_start=on_start, on_end=on_end))
    return Agent(
        name=name,
        model=model,
        instructions=load_prompt(prompt_name),
        hooks=hooks,
        mcpServers=mcp_servers or {},
    )


def build_agents(model: str) -> dict[str, Agent]:
    """Build all static agents used in the Story2Proposal workflow."""
    drawio_config = drawio_server_config()
    return {
        "architect": _make_agent(
            "architect",
            model,
            "architect.md",
            on_end="mcp__s2p_workflow__capture_architect_output",
        ),
        "section_writer": _make_agent(
            "section_writer",
            model,
            "section_writer.md",
            on_end="mcp__s2p_workflow__capture_section_writer_output",
            mcp_servers=({"drawio": drawio_config} if drawio_config is not None else None),
        ),
        "reasoning_evaluator": _make_agent(
            "reasoning_evaluator",
            model,
            "reasoning_evaluator.md",
            on_end="mcp__s2p_workflow__capture_reasoning_feedback",
        ),
        "data_fidelity_evaluator": _make_agent(
            "data_fidelity_evaluator",
            model,
            "data_fidelity_evaluator.md",
            on_end="mcp__s2p_workflow__capture_data_fidelity_feedback",
        ),
        "visual_evaluator": _make_agent(
            "visual_evaluator",
            model,
            "visual_evaluator.md",
            on_end="mcp__s2p_workflow__capture_visual_feedback",
        ),
        "review_controller": _make_agent(
            "review_controller",
            model,
            "review_controller.md",
            on_start="mcp__s2p_workflow__apply_review_cycle",
        ),
        "refiner": _make_agent(
            "refiner",
            model,
            "refiner.md",
            on_end="mcp__s2p_workflow__capture_refiner_output",
        ),
        "renderer": _make_agent(
            "renderer",
            model,
            "renderer.md",
            on_start="mcp__s2p_workflow__render_and_finalize",
        ),
    }
