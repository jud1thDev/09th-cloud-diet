from __future__ import annotations

import json
import os
import re
import subprocess
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


class HermesProvider(BaseProvider):
    """Hermes Agent CLI를 subprocess로 호출해 OAuth credential로 LLM에 접근한다.

    ANTHROPIC_API_KEY 없이 동작한다 — Hermes의 anthropic_billing_bypass 훅이
    credential pool(anthropic-oauth-*)을 사용해 호출을 처리한다.
    """

    name = "hermes"
    # hermes -z 출력 첫 줄에 종종 들어가는 banner/cwd 표시를 제거하기 위한 패턴.
    _BANNER_RE = re.compile(r"^\s*\[?[\w_-]+:\s*[^\]]+\]?\s*$")

    def complete(self, system: str, user: str) -> LLMUsage:
        prompt = f"{system}\n\n{user}"
        # 모델 지정은 ENV 강제 시에만. 미지정 시 Hermes config의 default (보통 opus-4-7).
        # claude-haiku-4-5 같은 짧은 이름은 404 반환 — 풀 alias 또는 'anthropic/...' 필요.
        argv = ["hermes", "-z", prompt, "--ignore-rules", "--ignore-user-config"]
        model = os.getenv("HERMES_MODEL")
        if model:
            argv += ["-m", model]
        try:
            result = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            return LLMUsage(self.name, estimate_tokens(prompt), 0, True, error="hermes timeout (180s)")
        except FileNotFoundError:
            return LLMUsage(self.name, estimate_tokens(prompt), 0, True, error="hermes binary not found in PATH")

        raw = (result.stdout or "").strip()
        # banner/메타 라인 제거
        lines = [ln for ln in raw.splitlines() if ln.strip() and not self._BANNER_RE.match(ln)]
        text = "\n".join(lines).strip()
        err = (result.stderr or "").strip() if result.returncode != 0 else None
        return LLMUsage(
            provider=self.name,
            input_tokens=estimate_tokens(prompt),
            output_tokens=estimate_tokens(text),
            estimated=True,
            text=text,
            error=err,
        )


def get_provider(name: str) -> BaseProvider:
    if name == "openai":
        return OpenAIProvider()
    if name == "claude":
        return ClaudeProvider()
    if name == "hermes":
        return HermesProvider()
    return BaseProvider()
