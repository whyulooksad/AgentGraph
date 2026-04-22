from __future__ import annotations

"""模型输出与结构化对象之间的轻量转换辅助函数。

Story2Proposal 的多个 Agent 会被要求输出 JSON，这个文件负责从模型文本
里提取 JSON 对象、校验成 Pydantic 模型，并在需要时把对象再格式化成
字符串。
"""

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def extract_json_object(text: str) -> dict[str, Any]:
    """从模型文本中提取第一个可解析的 JSON 对象。"""
    # 优先提取 ```json ... ``` 代码块；如果没有，再退回到正文中的对象。
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
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
