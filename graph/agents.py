from __future__ import annotations

"""Story2Proposal 应用层 Agent 定义。

这一层只负责声明图里有哪些 Agent、各自使用哪个 prompt，
以及它们在生命周期的哪个阶段挂接应用层 Hook。
"""

import sys

from src import Agent, Hook

from config import load_prompt


def workflow_server_config() -> dict[str, object]:
    """返回应用层 workflow MCP server 的启动配置。"""
    return {
        "command": sys.executable,
        "args": ["-m", "servers.workflow"],
    }


def _make_agent(
    name: str,
    model: str,
    prompt_name: str,
    *,
    on_start: str | None = None,
    on_end: str | None = None,
) -> Agent:
    """按统一规则构造一个应用层 Agent。"""
    hooks = []
    if on_start is not None or on_end is not None:
        hooks.append(Hook(on_start=on_start, on_end=on_end))
    return Agent(
        name=name,
        model=model,
        instructions=load_prompt(prompt_name),
        hooks=hooks,
    )


def build_agents(model: str) -> dict[str, Agent]:
    """构造 Story2Proposal 流程中所有静态 Agent 节点。

    各个 Agent 的职责如下：

    - architect: 根据输入 story 生成论文 blueprint
    - section_writer: 按当前章节 contract 生成章节草稿
    - reasoning_evaluator: 从论证和逻辑角度评审草稿
    - structure_evaluator: 从结构和组织角度评审草稿
    - visual_evaluator: 从图表和可视化角度评审草稿
    - review_controller: 聚合评审结果并决定下一跳
    - refiner: 在全部章节完成后做全局润色
    - renderer: 生成最终 markdown / latex 稿件
    """
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
        ),
        "reasoning_evaluator": _make_agent(
            "reasoning_evaluator",
            model,
            "reasoning_evaluator.md",
            on_end="mcp__s2p_workflow__capture_reasoning_feedback",
        ),
        "structure_evaluator": _make_agent(
            "structure_evaluator",
            model,
            "structure_evaluator.md",
            on_end="mcp__s2p_workflow__capture_structure_feedback",
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
            # review_controller 进入前先聚合评审结果并决定下一跳。
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
            # renderer 不再让模型补写终稿，而是在启动时直接渲染最终产物。
            on_start="mcp__s2p_workflow__render_and_finalize",
        ),
    }
