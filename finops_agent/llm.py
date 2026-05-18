from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass


@dataclass
class LLMUsage:
    provider: str
    input_tokens: int
    output_tokens: int
    estimated: bool
    text: str = ""
    error: str | None = None


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


class BaseProvider:
    name = "local"

    def complete(self, system: str, user: str) -> LLMUsage:
        return LLMUsage(
            provider=self.name,
            input_tokens=estimate_tokens(system + "\n" + user),
            output_tokens=0,
            estimated=True,
        )


class OpenAIProvider(BaseProvider):
    name = "openai"

    def complete(self, system: str, user: str) -> LLMUsage:
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            return LLMUsage(self.name, estimate_tokens(system + user), 0, True, error="OPENAI_API_KEY missing")
        payload = json.dumps(
            {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.1,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            return LLMUsage(
                provider=self.name,
                input_tokens=usage.get("prompt_tokens", estimate_tokens(system + user)),
                output_tokens=usage.get("completion_tokens", 0),
                estimated=not bool(usage),
                text=data["choices"][0]["message"]["content"],
            )
        except Exception as exc:  # pragma: no cover - network-dependent fallback
            return LLMUsage(self.name, estimate_tokens(system + user), 0, True, error=str(exc))


class ClaudeProvider(BaseProvider):
    name = "claude"

    def complete(self, system: str, user: str) -> LLMUsage:
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            return LLMUsage(self.name, estimate_tokens(system + user), 0, True, error="ANTHROPIC_API_KEY missing")
        payload = json.dumps(
            {
                "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
                "max_tokens": 512,
                "temperature": 0.1,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            text = "".join(block.get("text", "") for block in data.get("content", []))
            return LLMUsage(
                provider=self.name,
                input_tokens=usage.get("input_tokens", estimate_tokens(system + user)),
                output_tokens=usage.get("output_tokens", 0),
                estimated=not bool(usage),
                text=text,
            )
        except Exception as exc:  # pragma: no cover - network-dependent fallback
            return LLMUsage(self.name, estimate_tokens(system + user), 0, True, error=str(exc))


def get_provider(name: str) -> BaseProvider:
    if name == "openai":
        return OpenAIProvider()
    if name == "claude":
        return ClaudeProvider()
    return BaseProvider()
