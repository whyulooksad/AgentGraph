from __future__ import annotations

"""Story2Proposal 的执行期 contract 模型。

这一层把 blueprint 进一步收敛成可执行、可追踪、可校验的稿件约束，用于
后续写作、评审、修订和渲染阶段。
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class StyleGuide(BaseModel):
    """整篇稿件共享的全局风格约束。"""
    tone: str = "scientific"
    citation_style: str = "author-year placeholder"
    section_style: str = "structured"
    figure_policy: str = "use explicit placeholders until real figures are available"


class SectionContract(BaseModel):
    """执行期单个章节的写作 contract。"""
    section_id: str
    title: str
    purpose: str
    required_claims: list[str] = Field(default_factory=list)
    required_evidence_ids: list[str] = Field(default_factory=list)
    required_visual_ids: list[str] = Field(default_factory=list)
    required_citation_ids: list[str] = Field(default_factory=list)
    depends_on_sections: list[str] = Field(default_factory=list)
    status: str = "pending"
    draft_path: str | None = None
    latest_draft_version: int = 0


class VisualArtifact(BaseModel):
    """执行期单个视觉资产的 contract 表达。"""
    artifact_id: str
    kind: str
    label: str
    caption_brief: str
    semantic_role: str
    source_evidence_ids: list[str] = Field(default_factory=list)
    target_sections: list[str] = Field(default_factory=list)
    placement_hint: str | None = None
    render_status: str = "planned"


class CitationSlot(BaseModel):
    """执行期单个引用位对象。"""
    citation_id: str
    citation_key: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    venue: str | None = None


class ClaimEvidenceLink(BaseModel):
    """claim 与 supporting evidence 的绑定关系。"""
    claim_id: str
    claim_text: str
    evidence_ids: list[str] = Field(default_factory=list)
    section_id: str
    verified: bool = False


class ValidationRule(BaseModel):
    """contract 内建的一条校验规则。"""
    rule_id: str
    rule_type: str
    description: str
    severity: str = "warning"
    enabled: bool = True


class RevisionRecord(BaseModel):
    """contract 在运行中的一条修订记录。"""
    stage: str
    agent: str
    summary: str
    affected_sections: list[str] = Field(default_factory=list)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ManuscriptContract(BaseModel):
    """整篇稿件在执行期的根 contract 对象。"""
    contract_id: str
    version: int = 1
    paper_title: str | None = None
    target_venue: str | None = None
    style_guide: StyleGuide = Field(default_factory=StyleGuide)
    sections: list[SectionContract] = Field(default_factory=list)
    visuals: list[VisualArtifact] = Field(default_factory=list)
    citations: list[CitationSlot] = Field(default_factory=list)
    glossary: list[str] = Field(default_factory=list)
    claim_evidence_links: list[ClaimEvidenceLink] = Field(default_factory=list)
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    revision_log: list[RevisionRecord] = Field(default_factory=list)
    global_status: dict[str, str] = Field(default_factory=dict)
