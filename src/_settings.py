from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, InitSettingsSource, SettingsConfigDict

from .types import MCPServer

ROOT_DIR = Path(__file__).resolve().parents[1]


def json_merge(left: dict[str, Any], *rights: dict[str, Any]) -> dict[str, Any]:
    """递归合并类 JSON 对象"""
    result: dict[str, Any] = dict(left)
    for right in rights:
        for key, right_val in right.items():
            left_val = result.get(key)
            if (
                isinstance(left_val, dict)
                and isinstance(right_val, dict)
                and key == "mcpServers"
            ):
                result[key] = json_merge(left_val, right_val)
            else:
                result[key] = right_val
    return result


class ClaudeCodeSettingsSource(InitSettingsSource):
    """加载本地配置文件"""
    def __init__(self, settings_cls: type[BaseModel]):
        user_config: dict[str, Any] = {}
        local_config: dict[str, Any] = {}
        project_config: dict[str, Any] = {}
        if (dot_claude_json := Path.home() / ".claude.json").exists():
            try:
                user_config = json.loads(dot_claude_json.read_text(encoding="utf-8"))
                local_config = user_config.get("projects", {}).get(str(Path.cwd()), {})
            except Exception:
                pass
        if (dot_mcp_json := ROOT_DIR / ".mcp.json").exists():
            try:
                project_config = json.loads(dot_mcp_json.read_text(encoding="utf-8"))
            except Exception:
                pass
        super().__init__(
            settings_cls,
            json_merge(user_config, local_config, project_config),
        )


class Settings(BaseSettings):
    """基础配置"""
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str | None = None
    mcp_servers: dict[str, MCPServer] = Field(default_factory=dict, alias="mcpServers")
    agents_md: Path | list[Path] = ROOT_DIR / "AGENTS.md"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            ClaudeCodeSettingsSource(settings_cls),
        )

    def get_agents_md_content(self) -> str:
        """读取 AGENTS.md 文件，并将其拼接为 Markdown 块"""
        if isinstance(self.agents_md, Path):
            agents_mds = [self.agents_md]
        else:
            agents_mds = self.agents_md
        contents: list[str] = []
        for agent_md in agents_mds:
            if agent_md.exists():
                try:
                    contents.append(
                        f'```markdown title="{agent_md}"\n'
                        f'{agent_md.read_text(encoding="utf-8").strip()}\n'
                        '```'
                    )
                except Exception:
                    pass
        return "\n\n".join(contents)


settings = Settings()
