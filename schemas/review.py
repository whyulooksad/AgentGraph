from __future__ import annotations

"""Story2Proposal 的评审反馈模型。

这一层定义 evaluator 阶段的结构化输出，包括问题项、建议动作和可以直接
作用到 contract 的 patch。
"""

from typing import Literal

from pydantic import BaseModel, Field


class IssueItem(BaseModel):
    """一条具体问题项。"""
    issue_id: str
    description: str
    severity: Literal["low", "medium", "high"] = "medium"


class SuggestedAction(BaseModel):
    """一条建议动作。"""
    action: str
    rationale: str | None = None


class ContractPatch(BaseModel):
    """一条可直接应用到 contract 的结构化 patch。"""
    patch_type: Literal[
        "append_glossary",
        "set_section_status",
        "add_required_citation",
        "add_required_visual",
        "mark_claim_verified",
    ]
    target_id: str
    value: str


class EvaluationFeedback(BaseModel):
    """一次 evaluator 输出的完整结构化反馈。"""
    evaluator_type: str
    status: Literal["pass", "revise", "fail"]
    score: float | None = None
    issues: list[IssueItem] = Field(default_factory=list)
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    contract_patches: list[ContractPatch] = Field(default_factory=list)
