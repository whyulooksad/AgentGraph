from __future__ import annotations

"""模型输出与结构化对象之间的转换工具。

这个文件负责提取 JSON、校验模型和格式化输出。
"""

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def extract_json_object(text: str) -> dict[str, Any]:
    """从模型文本中提取第一个可解析的 JSON 对象。"""
    # 优先提取代码块中的 JSON。
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    # 如果没有代码块，再退回正文中的对象片段。
    candidates = fenced or re.findall(r"(\{.*\})", text, flags=re.S)
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("No valid JSON object found in model output.")


def parse_model(text: str, model_type: type[T]) -> T:
    """把模型文本解析并校验成指定的 Pydantic 模型。"""
    payload = extract_json_object(text)
    return model_type.model_validate(payload)


def json_dumps(value: Any) -> str:
    """把任意对象稳定格式化成 JSON 字符串。"""
    if isinstance(value, BaseModel):
        return value.model_dump_json(indent=2)
    return json.dumps(value, ensure_ascii=False, indent=2)
