"""极简 LLM 封装：读 .env 拿凭证，chat() 返回原始响应 dict，tools 经 extra_body 透传。"""

from pathlib import Path
from typing import Any

from voyo.model import AnthropicClient

_ROOT = Path(__file__).resolve().parents[1]


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in (_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip():
            env[key.strip()] = value.strip()
    return env


class LLM:
    def __init__(self) -> None:
        env = load_env()
        self.model = env["ANTHROPIC_MODEL"]
        self._client = AnthropicClient(
            base_url=env["ANTHROPIC_BASE_URL"], api_key=env["ANTHROPIC_AUTH_TOKEN"]
        )

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
        thinking_enabled :bool= False
    ) -> dict[str, Any]:
        extra = {"tools": tools} if tools else None
        return self._client.chat(
            model=self.model,
            messages=messages,
            system=system,
            extra_body=extra,
            max_tokens=max_tokens,
            thinking_enabled=thinking_enabled
        )
