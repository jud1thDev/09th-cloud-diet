"""Track B 식 Observability — events.jsonl + run_id trace.

각 파이프라인 실행마다 run_id를 발급하고 stage start/end·LLM 호출·warning을
JSON Lines 한 줄에 이벤트 하나로 누적한다. SVG의 Observability layer (3 pillars 중
② Logs)에 해당하며, run_id는 모든 이벤트에 박혀 trace 역할을 한다.

분석 예) jq로 단계별 지속 시간 보기:
    jq -c 'select(.event | endswith(".end")) | {event, duration_ms}' events.jsonl
"""

from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def _new_run_id() -> str:
    return f"r-{uuid.uuid4().hex[:8]}"


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class EventLogger:
    """events.jsonl 한 줄에 이벤트 하나. 모든 이벤트는 같은 run_id를 공유한다.

    span() 컨텍스트 매니저로 stage start/end를 자동 짝지어준다. close()를
    호출하면 run.end가 마지막 줄로 박혀 trace가 닫힌다.
    """

    def __init__(
        self,
        output_dir: Path,
        *,
        run_id: str | None = None,
        scenario_id: str | None = None,
        week: int | None = None,
        mode: str | None = None,
        provider: str | None = None,
        path_name: str = "events.jsonl",
    ) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        self.path = output_dir / path_name
        self._fp = self.path.open("a", encoding="utf-8")
        self.run_id = run_id or _new_run_id()
        self.scenario_id = scenario_id
        self.week = week
        self._seq = 0
        self._t0 = time.perf_counter()
        self._closed = False
        self.event("run.start", mode=mode, provider=provider)

    def event(self, name: str, **fields: Any) -> None:
        """한 줄 JSON 이벤트를 append. None 필드는 떨군다 (잡음 줄이기)."""
        if self._closed:
            return
        record: dict[str, Any] = {
            "ts": _now_iso(),
            "ts_offset_ms": round((time.perf_counter() - self._t0) * 1000, 3),
            "seq": self._seq,
            "run_id": self.run_id,
            "event": name,
        }
        if self.scenario_id is not None:
            record["scenario_id"] = self.scenario_id
        if self.week is not None:
            record["week"] = self.week
        for k, v in fields.items():
            if v is None:
                continue
            record[k] = v
        self._fp.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._fp.flush()
        self._seq += 1

    @contextmanager
    def span(self, name: str, **start_fields: Any) -> Iterator[dict[str, Any]]:
        """`{name}.start` → 사용자 코드 → `{name}.end` (duration_ms 자동).

        with logger.span("detect") as carry:
            findings = collect()
            carry["findings_count"] = len(findings)
        """
        carry: dict[str, Any] = {}
        self.event(f"{name}.start", **start_fields)
        start = time.perf_counter()
        try:
            yield carry
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            self.event(f"{name}.end", duration_ms=duration_ms, error=str(exc), **carry)
            raise
        else:
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            self.event(f"{name}.end", duration_ms=duration_ms, **carry)

    def close(self, **summary: Any) -> None:
        if self._closed:
            return
        self.event("run.end", **summary)
        self._closed = True
        self._fp.close()

    def __enter__(self) -> "EventLogger":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close(status="error" if exc else "ok")
