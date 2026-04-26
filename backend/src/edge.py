from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Edge(BaseModel):
    """执行图中的边

    使用这类节点来创建从 source 节点到 target 节点的控制流转移关系
    如果 source 是字符串元组，表示需要所有 source 都完成后，才会触发 target。
    """

    model_config = ConfigDict(frozen=True)

    source: str | tuple[str, ...]
    target: str

    @classmethod
    def as_tool(cls) -> dict[str, object]:
        """把 Edge 暴露成 create_edge 内建工具"""
        return {
            "type": "function",
            "function": {
                "name": "create_edge",
                "description": cls.__doc__ or "",
                "parameters": cls.model_json_schema(),
            },
        }
