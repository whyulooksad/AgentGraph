from typing import Any, Literal, Required, TypedDict

from mcp.client.stdio import StdioServerParameters
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from openai.types.chat.chat_completion_stream_options_param import (
    ChatCompletionStreamOptionsParam,
)
from openai.types.chat.chat_completion_tool_choice_option_param import (
    ChatCompletionToolChoiceOptionParam,
)
from openai.types.chat.completion_create_params import ResponseFormat
from pydantic import BaseModel


class SSEServer(BaseModel):
    """SSE MCP 服务端配置"""

    type: Literal["sse"]
    url: str
    headers: dict[str, str] | None = None


MCPServer = StdioServerParameters | SSEServer


class CompletionCreateParams(TypedDict, total=False):
    """Agent.__call__允许传入的参数"""

    messages: Required[list[ChatCompletionMessageParam]]
    stream: bool
    frequency_penalty: float | None
    logprobs: bool | None
    max_tokens: int | None
    presence_penalty: float | None
    response_format: ResponseFormat | Any | None
    seed: int | None
    stop: str | list[str] | None
    stream_options: ChatCompletionStreamOptionsParam | None
    temperature: float | None
    tool_choice: ChatCompletionToolChoiceOptionParam | None
    top_logprobs: int | None
    top_p: float | None
    tools: list[ChatCompletionToolParam]


class MessagesState(TypedDict):
    """节点间传递的消息状态"""

    messages: list[ChatCompletionMessageParam]
