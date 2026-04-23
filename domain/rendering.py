from __future__ import annotations

"""Story2Proposal 的最终稿渲染辅助函数。

这个模块负责把累积好的 contract、draft 和 refiner 产物组织成可输出的
markdown 与 LaTeX 稿件。
"""

from typing import Any

from schemas import RenderedManuscript


def _get_writing_language(context: dict[str, Any]) -> str:
    """读取最终稿件的目标语言。"""
    story = context.get("story") or {}
    metadata = story.get("metadata") or {}
    language = metadata.get("writing_language")
    return language if language in {"en", "zh"} else "en"


def _references_heading(language: str) -> str:
    """返回参考文献章节标题。"""
    return "参考文献" if language == "zh" else "References"


def _unknown_authors_label(language: str) -> str:
    """返回作者缺失时的兜底文案。"""
    return "未知作者" if language == "zh" else "Unknown"


def _unknown_year_label(language: str) -> str:
    """返回年份缺失时的兜底文案。"""
    return "未知年份" if language == "zh" else "n.d."


def build_bibliography_block(context: dict[str, Any]) -> str:
    """把 contract 里的 citation slot 渲染成 markdown 参考文献列表。"""
    contract = context.get("contract") or {}
    language = _get_writing_language(context)
    lines = []
    for item in contract.get("citations", []):
        authors = ", ".join(item.get("authors", [])) or _unknown_authors_label(language)
        year = item.get("year") or _unknown_year_label(language)
        venue = f". {item['venue']}" if item.get("venue") else ""
        lines.append(
            f"- [{item['citation_key']}] {authors} ({year}). {item['title']}{venue}."
        )
    return "\n".join(lines)


def render_latex_from_markdown(
    title: str,
    sections: list[dict[str, Any]],
    drafts: dict[str, Any],
    bibliography: str,
    abstract_override: str | None,
    writing_language: str,
) -> str:
    """根据当前稿件状态构造一个轻量 LaTeX scaffold。"""
    body: list[str] = [
        r"\documentclass{article}",
        r"\usepackage[utf8]{inputenc}",
        r"\begin{document}",
        rf"\title{{{title}}}",
        r"\maketitle",
    ]
    for section in sections:
        draft = drafts.get(section["section_id"])
        if draft is None:
            continue
        content = draft["content"]
        if section["section_id"] == "abstract" and abstract_override:
            content = abstract_override
        body.append(rf"\section{{{draft['title']}}}")
        body.append(content.replace("_", r"\_"))
    if bibliography:
        body.append(rf"\section{{{_references_heading(writing_language)}}}")
        body.append(bibliography.replace("_", r"\_"))
    body.append(r"\end{document}")
    return "\n".join(body) + "\n"


def render_markdown_manuscript(context: dict[str, Any]) -> RenderedManuscript:
    """组装最终 markdown 稿件及其对应的 LaTeX 版本。"""
    contract = context.get("contract") or {}
    drafts = context.get("drafts") or {}
    sections = []
    warnings: list[str] = []
    writing_language = _get_writing_language(context)
    title = (
        contract.get("paper_title")
        or context.get("story", {}).get("title_hint")
        or "Untitled Manuscript"
    )
    sections.append(f"# {title}")
    refiner_output = context.get("artifacts", {}).get("refiner_output", {})
    abstract_override = context.get("artifacts", {}).get("abstract_override")
    for section in contract.get("sections", []):
        draft = drafts.get(section["section_id"])
        if draft is None:
            warnings.append(f"Missing draft for section {section['section_id']}")
            continue
        content = draft["content"]
        # refiner 可以单独给出一版更收敛的 abstract，而不用重写
        # 其他 section draft。
        if section["section_id"] == "abstract" and abstract_override:
            content = abstract_override
        if section["section_id"] in refiner_output.get("section_notes", {}):
            content = (
                f"{content}\n\n> Refiner note: "
                f"{refiner_output['section_notes'][section['section_id']]}"
            )
        sections.append(f"## {draft['title']}\n\n{content}")
    bibliography = build_bibliography_block(context)
    if bibliography:
        sections.append(f"## {_references_heading(writing_language)}\n\n" + bibliography)
    markdown = "\n\n".join(sections).strip() + "\n"
    latex = render_latex_from_markdown(
        title,
        contract.get("sections", []),
        drafts,
        bibliography,
        abstract_override,
        writing_language,
    )
    return RenderedManuscript(markdown=markdown, latex=latex, warnings=warnings)
