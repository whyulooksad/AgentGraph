"""通用辅助函数"""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, TypeVar

T = TypeVar("T")


def completion_to_message(completion: Any) -> dict[str, Any]:
    """把 chat completion 对象转换成框架内部 assistant 消息"""
    if isinstance(completion, dict):
        return completion

    choices = getattr(completion, "choices", None)
    if not choices:
        raise ValueError("ChatCompletion has no choices")
    choice = choices[0]
    message = choice.message

    result: dict[str, Any] = {"role": "assistant"}
    if getattr(message, "content", None):
        result["content"] = message.content
    if getattr(message, "tool_calls", None) is not None:
        tool_calls: list[dict[str, Any]] = []
        for tool_call in message.tool_calls:
            if getattr(tool_call, "function", None) is not None:
                tool_calls.append(
                    {
                        "type": "function",
                        "id": tool_call.id,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                )
            else:
                tool_calls.append(
                    {
                        "type": "custom",
                        "id": tool_call.id,
                        "custom": {
                            "name": tool_call.custom.name,
                            "input": tool_call.custom.input,
                        },
                    }
                )
        result["tool_calls"] = tool_calls
    return result


def now() -> int:
    """OpenAI 兼容的整型时间戳"""
    return int(datetime.now().timestamp())


RANDOM_STRING_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def get_random_string(length: int, allowed_chars: str = RANDOM_STRING_CHARS) -> str:
    """生成安全随机字符串"""
    return "".join(secrets.choice(allowed_chars) for _ in range(length))


async def read_into_queue(
    task: AsyncGenerator[T, None],
    queue: asyncio.Queue[T],
    done: asyncio.Semaphore,
) -> None:
    """把异步生成器内容读入共享队列"""
    async for item in task:
        await queue.put(item)
    await done.acquire()


async def join(*generators: AsyncGenerator[T, None]) -> AsyncGenerator[T, None]:
    """把多个异步生成器合并成一个"""
    queue: asyncio.Queue[T] = asyncio.Queue(maxsize=1)
    done_semaphore = asyncio.Semaphore(len(generators))
    produce_tasks = [
        asyncio.create_task(read_into_queue(task, queue, done_semaphore))
        for task in generators
    ]

    while not done_semaphore.locked() or not queue.empty():
        try:
            yield await asyncio.wait_for(queue.get(), 0.001)
        except TimeoutError:
            continue

    try:
        await asyncio.wait_for(asyncio.gather(*produce_tasks), 0)
    except TimeoutError as exc:
        raise NotImplementedError(
            "Impossible state: expected all tasks to be exhausted"
        ) from exc
