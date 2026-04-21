from __future__ import annotations

"""Story2Proposal 的写作产物模型。

这一层承载 section writer、refiner 和 renderer 的结构化输出，让后续
review、render 和持久化逻辑可以直接消费这些结果。
"""

from pydantic import BaseModel, Field


class SectionDraft(BaseModel):
    """section writer 产出的单个章节草稿。"""
    section_id: str
    title: str
    content: str
    referenced_visual_ids: list[str] = Field(default_factory=list)
    referenced_citation_ids: list[str] = Field(default_factory=list)
    covered_claim_ids: list[str] = Field(default_factory=list)


class RefinerOutput(BaseModel):
    """refiner 产出的全局收束结果。"""
    abstract_override: str | None = None
    section_notes: dict[str, str] = Field(default_factory=dict)
    global_notes: list[str] = Field(default_factory=list)


class RenderedManuscript(BaseModel):
    """renderer 产出的最终稿件。"""
    markdown: str
    latex: str
    warnings: list[str] = Field(default_factory=list)
