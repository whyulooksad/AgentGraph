from __future__ import annotations

"""Story2Proposal 应用层图构建。

这一层只负责把静态 Agent 节点和 Edge 组装成完整流程图，
不负责业务状态推进和 Hook 逻辑。
"""

from src import Agent, Edge

from config import load_prompt

from .agents import build_agents, workflow_server_config


def build_story2proposal_graph(model: str) -> Agent:
    """构造 Story2Proposal 的根图。

    根节点 `orchestrator` 挂应用层 workflow server，并持有整张静态子图。
    具体状态更新通过子 Agent 的 Hook 落到 `servers/` 和 `domain/`。

    """
    agents = build_agents(model)
    return Agent(
        name="orchestrator",
        model=model,
        instructions=load_prompt("orchestrator.md"),
        mcpServers={"s2p_workflow": workflow_server_config()},
        nodes=set(agents.values()),
        edges={
            Edge(source="orchestrator", target="architect"),
            Edge(source="architect", target="section_writer"),
            Edge(source="section_writer", target="reasoning_evaluator"),
            Edge(source="section_writer", target="structure_evaluator"),
            Edge(source="section_writer", target="visual_evaluator"),
            Edge(
                # 三个 evaluator 都完成后，才能统一进入 review_controller。
                source=("reasoning_evaluator", "structure_evaluator", "visual_evaluator"),
                target="review_controller",
            ),
            # 下一跳由 review cycle 写入 runtime.next_node，再由 CEL 解析。
            Edge(source="review_controller", target="runtime.next_node"),
            Edge(source="refiner", target="renderer"),
        },
    )
