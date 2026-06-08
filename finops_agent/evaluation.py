"""Track B 식 Evaluation 트랙 — E1 Golden Set + E2 LLM-judge.

E1: README 선언 패턴 ID를 ground truth로 두고 finding patterns_found와 비교 →
    precision/recall/f1. blind recall은 아니지만 회귀 감지에는 충분히 쓸 만하다.
E2: writer가 만든 narrative를 별도 LLM (narrative-judge 카드)이 5점 척도로
    채점. provider가 local이면 건너뛴다 (로컬에는 채점할 LLM이 없으므로).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .llm import BaseProvider
from .models import Bundle, EmergentFinding, Finding


_JUDGE_CARD_PATH = Path(__file__).resolve().parent / "agents" / "narrative-judge.md"


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def golden_set_eval(bundle: Bundle, findings: list[Finding]) -> dict[str, Any]:
    """README pattern_ids를 ground truth로 precision/recall/f1을 계산한다.

    LV-006 같은 시즌 2 sub-pattern (LV-006-TA-EBS 등)은 declared prefix가
    매치되면 cover로 본다 — build_measurements의 declared_pattern_coverage와
    같은 규칙. extras는 declared 어느 prefix와도 안 맞는 found만 잡는다.
    """
    expected = sorted(set(bundle.pattern_ids))
    found = sorted({f.pattern_id for f in findings})
    found_set = set(found)

    def _covered(declared: str) -> bool:
        if declared in found_set:
            return True
        return any(p.startswith(declared + "-") for p in found_set)

    matched = [d for d in expected if _covered(d)]
    missed = [d for d in expected if d not in matched]
    extra = [
        p
        for p in found
        if p not in expected and not any(p.startswith(d + "-") for d in expected)
    ]

    tp = len(matched)
    fp = len(extra)
    fn = len(missed)
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision and recall
        else None
    )

    return {
        "expected": expected,
        "found": found,
        "matched": matched,
        "missed": missed,
        "extra": extra,
        "precision": round(precision, 3) if precision is not None else None,
        "recall": round(recall, 3) if recall is not None else None,
        "f1": round(f1, 3) if f1 is not None else None,
        "basis": "README-declared scenario components; not blind recall",
    }


def _load_judge_system() -> str:
    """카드 frontmatter를 잘라내고 본문만 system prompt로 반환한다."""
    text = _JUDGE_CARD_PATH.read_text(encoding="utf-8")
    match = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
    return text[match.end():].lstrip("\n") if match else text


def judge_narrative(
    narrative: str,
    findings: list[Finding],
    emergent: list[EmergentFinding],
    provider: BaseProvider,
) -> dict[str, Any]:
    """별도 LLM이 narrative를 factuality·clarity·completeness 5점 척도로 채점.

    provider가 local이거나 narrative가 비어 있으면 skipped=True로 메타만 반환한다.
    LLM이 JSON을 못 뱉으면 raw 일부와 함께 skipped로 마킹 — 측정값은 늘 채워서
    measurements.json에 박힌다.
    """
    if not narrative:
        return {"skipped": True, "reason": "no narrative"}
    if provider.name == "local":
        return {"skipped": True, "reason": "local provider has no LLM"}

    system = _load_judge_system()
    payload = {
        "narrative": narrative,
        "findings": [
            {
                "pattern_id": f.pattern_id,
                "title": f.title,
                "severity": f.severity,
                "resource": f.resource,
                "estimated_savings": f.estimated_savings,
            }
            for f in findings
        ],
        "emergent": [{"title": e.title, "chain": e.chain} for e in emergent],
    }
    user = json.dumps(payload, ensure_ascii=False, indent=2)

    llm = provider.complete(system, user)
    if llm.error or not llm.text:
        return {
            "skipped": True,
            "reason": llm.error or "empty response",
            "llm_input_tokens": llm.input_tokens,
            "llm_output_tokens": llm.output_tokens,
            "llm_tokens_estimated": llm.estimated,
        }
    try:
        parsed = json.loads(_strip_code_fence(llm.text))
    except (ValueError, KeyError) as exc:
        return {
            "skipped": True,
            "reason": f"parse error: {exc}",
            "raw": llm.text[:200],
            "llm_input_tokens": llm.input_tokens,
            "llm_output_tokens": llm.output_tokens,
            "llm_tokens_estimated": llm.estimated,
        }
    parsed["llm_input_tokens"] = llm.input_tokens
    parsed["llm_output_tokens"] = llm.output_tokens
    parsed["llm_tokens_estimated"] = llm.estimated
    return parsed
