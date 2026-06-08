"""Agentic 파이프라인 오케스트레이터 — 3축(agents/skills/orchestrator) 골격.

W2 2단계 스켈레톤. detector 호출은 기존 함수 그대로 재사용하고, LLM 호출
(reviewer/writer)은 placeholder로 둔다. W2 3~5단계에서 카드 본문과 LLM
호출 본체를 채운다.

흐름 요약:
    1. agents/*.md 카드 로드(YAML frontmatter + 마크다운 본문)
    2. 도메인 카드의 detector_fns를 dedup해 한 번씩만 실행
    3. 카드별로 patterns 필터링 → finding 풀
    4. analyzers.correlate()로 EmergentFinding 도출
    5. cost-reviewer 카드로 finding 검수 (placeholder)
    6. solution-writer 카드로 report 본문 작성 (placeholder)
    7. artifacts.write_artifacts()로 산출물 일괄 생성
"""

from __future__ import annotations

import inspect
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import detectors
from .analyzers import correlate
from .artifacts import write_artifacts
from .evaluation import golden_set_eval, judge_narrative
from .llm import BaseProvider, estimate_tokens
from .models import AnalyzerResult, Bundle, EmergentFinding, Finding, PipelineResult
from .observability import EventLogger


AGENTS_DIR = Path(__file__).resolve().parent / "agents"
SKILLS_DIR = Path(__file__).resolve().parent / "skills"

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


@dataclass
class AgentCard:
    """agents/*.md 한 장. frontmatter + 본문 + resolve된 detector callable."""

    name: str
    role: str  # "expert" | "reviewer" | "writer"
    domain: str | None
    patterns: list[str]
    detector_fns: list[Callable]
    body: str
    source: Path


@dataclass
class SkillCard:
    """skills/*.md 한 장. 여러 에이전트가 컨텍스트로 가져다 쓴다."""

    name: str
    body: str
    source: Path


def _parse_scalar(value: str) -> Any:
    """frontmatter scalar 값을 파이썬 타입으로. 인용부호 제거 + int/None만 처리."""
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.lstrip("-").isdigit():
        return int(value)
    return value


def _parse_frontmatter(raw: str) -> dict[str, Any]:
    """카드 frontmatter용 최소 파서. scalar + inline list만 지원.

    PyYAML 의존을 피하기 위한 작은 파서다. 카드가 복잡해지면 PyYAML로 교체.
    """
    out: dict[str, Any] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if not value:
            out[key] = None
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            out[key] = (
                [_parse_scalar(item) for item in inner.split(",") if item.strip()]
                if inner
                else []
            )
            continue
        out[key] = _parse_scalar(value)
    return out


def _parse_card(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path}: frontmatter(---) 블록이 없습니다.")
    front = _parse_frontmatter(match.group(1))
    body = text[match.end():].lstrip("\n")
    return front, body


def _resolve_detector_fns(names: list[str]) -> list[Callable]:
    fns: list[Callable] = []
    for name in names or []:
        fn = getattr(detectors, name, None)
        if fn is None or not callable(fn):
            raise ValueError(
                f"detectors.{name} 함수가 없습니다. 카드 frontmatter의 detector_fns를 확인하세요."
            )
        fns.append(fn)
    return fns


def _infer_role(name: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    if name.endswith("-expert"):
        return "expert"
    if name == "cost-reviewer":
        return "reviewer"
    if name == "solution-writer":
        return "writer"
    return "other"


def load_agent_cards(agents_dir: Path = AGENTS_DIR) -> list[AgentCard]:
    cards: list[AgentCard] = []
    for path in sorted(agents_dir.glob("*.md")):
        front, body = _parse_card(path)
        name = front.get("name") or path.stem
        cards.append(
            AgentCard(
                name=name,
                role=_infer_role(name, front.get("role")),
                domain=front.get("domain"),
                patterns=list(front.get("patterns") or []),
                detector_fns=_resolve_detector_fns(front.get("detector_fns") or []),
                body=body,
                source=path,
            )
        )
    return cards


def load_skill(name: str, skills_dir: Path = SKILLS_DIR) -> SkillCard:
    path = skills_dir / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"skill not found: {path}")
    _, body = _parse_card(path)
    return SkillCard(name=name, body=body, source=path)


def _run_detector(fn: Callable, bundle: Bundle) -> list[Finding]:
    """detector 시그니처에 따라 component 단위 또는 bundle 단위로 실행한다.

    detect_lv006·detect_bundle_globals는 (Bundle,) 한 인자, 나머지는
    (Component, Bundle) 두 인자라서 매개변수 개수로 분기한다.
    """
    params = inspect.signature(fn).parameters
    if len(params) == 1:
        return list(fn(bundle))
    findings: list[Finding] = []
    for component in bundle.components:
        findings.extend(fn(component, bundle))
    return findings


def _collect_findings(
    domain_cards: list[AgentCard],
    bundle: Bundle,
) -> tuple[list[Finding], dict[str, list[Finding]]]:
    """도메인 카드의 detector를 dedup해 한 번씩만 호출하고, 카드별로 필터한다.

    detect_lv006처럼 여러 카드가 공유하는 함수는 중복 호출 없이 한 번만 실행하고,
    각 카드의 patterns 리스트에 든 finding만 그 카드의 결과로 묶는다.
    """
    cache: dict[int, list[Finding]] = {}
    for card in domain_cards:
        for fn in card.detector_fns:
            key = id(fn)
            if key not in cache:
                cache[key] = _run_detector(fn, bundle)

    all_findings: list[Finding] = []
    seen_ids: set[int] = set()
    for findings in cache.values():
        for finding in findings:
            if id(finding) in seen_ids:
                continue
            seen_ids.add(id(finding))
            all_findings.append(finding)

    by_card: dict[str, list[Finding]] = defaultdict(list)
    for card in domain_cards:
        wanted = set(card.patterns)
        if not wanted:
            continue
        for fn in card.detector_fns:
            for finding in cache[id(fn)]:
                if finding.pattern_id in wanted:
                    by_card[card.name].append(finding)
    return all_findings, by_card


def _finding_payload(f: Finding) -> dict[str, Any]:
    """LLM에 보낼 finding 요약 (토큰 절약을 위해 selective)."""
    return {
        "pattern_id": f.pattern_id,
        "title": f.title,
        "resource": f.resource,
        "severity": f.severity,
        "evidence": f.evidence,
        "recommendation": f.recommendation,
        "estimated_savings": f.estimated_savings,
    }


def _emergent_payload(e: EmergentFinding) -> dict[str, Any]:
    return {
        "title": e.title,
        "detail": e.detail,
        "chain": e.chain,
        "recommendation": e.recommendation,
    }


def _strip_code_fence(text: str) -> str:
    """LLM 출력에서 ```json...``` 또는 ```...``` 펜스만 벗긴다."""
    text = text.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _review_findings(
    reviewer: AgentCard,
    findings: list[Finding],
    provider: BaseProvider,
) -> tuple[list[Finding], dict[str, Any]]:
    """cost-reviewer 카드 본문을 system, findings JSON을 user로 LLM 호출.

    Finding 자체는 회귀 안전을 위해 입력 그대로 반환한다. 응답에서 받은
    confidence·review_notes는 사이드 dict로 반환해 measurements 산출물에 끼울 수 있다.
    """
    review_meta: dict[str, Any] = {"reviewed": False, "by": reviewer.name, "items": []}
    if not findings:
        return findings, review_meta
    if provider.name == "local":
        review_meta["skipped"] = True
        review_meta["reason"] = "local provider has no LLM"
        return findings, review_meta

    system = reviewer.body
    payload = {"findings": [_finding_payload(f) for f in findings]}
    user = json.dumps(payload, ensure_ascii=False, indent=2)

    last_error: str | None = None
    for attempt in range(2):
        llm = provider.complete(system, user)
        if llm.error:
            last_error = llm.error
            review_meta["llm_input_tokens"] = llm.input_tokens
            review_meta["llm_output_tokens"] = llm.output_tokens
            review_meta["llm_tokens_estimated"] = llm.estimated
            break
        if not llm.text:
            last_error = "empty response"
            review_meta["llm_input_tokens"] = llm.input_tokens
            review_meta["llm_output_tokens"] = llm.output_tokens
            review_meta["llm_tokens_estimated"] = llm.estimated
            break
        try:
            parsed = json.loads(_strip_code_fence(llm.text))
            items = parsed.get("findings", [])
            if isinstance(items, list) and len(items) == len(findings):
                review_meta = {
                    "reviewed": True,
                    "by": reviewer.name,
                    "items": items,
                    "llm_input_tokens": llm.input_tokens,
                    "llm_output_tokens": llm.output_tokens,
                    "llm_tokens_estimated": llm.estimated,
                }
                return findings, review_meta
            last_error = f"finding count mismatch (got {len(items) if isinstance(items, list) else 'non-list'})"
        except (ValueError, KeyError) as exc:
            last_error = f"parse error: {exc}"
        user = user + "\n\nReturn ONLY valid JSON with the exact schema above. No commentary."

    review_meta["error"] = last_error
    return findings, review_meta


def _fallback_narrative(
    findings: list[Finding],
    emergent: list[EmergentFinding],
) -> str:
    """local provider용 deterministic 요약. LLM 없이도 agentic report가 비지 않게 한다."""
    if not findings and not emergent:
        return ""
    high_priority = [
        finding
        for finding in findings
        if finding.severity in {"critical", "high"}
    ] or findings
    lines = [
        f"{len(findings)}개 리소스에서 {len(set(f.pattern_id for f in findings))}개 FinOps 패턴을 확인했다."
    ]
    for finding in high_priority[:3]:
        savings = (
            f"월 ${finding.estimated_savings:.2f} 절감"
            if finding.estimated_savings
            else "절감액은 별도 검증"
        )
        lines.append(
            f"- `{finding.pattern_id}` `{finding.resource}`: {finding.title}. {finding.recommendation} ({savings})."
        )
    if emergent:
        lines.append(
            f"- 결합 원인: {emergent[0].chain}. {emergent[0].recommendation}"
        )
    return "\n".join(lines)


def _write_narrative(
    writer: AgentCard,
    findings: list[Finding],
    emergent: list[EmergentFinding],
    provider: BaseProvider,
) -> tuple[str, dict[str, Any]]:
    """solution-writer 카드 본문을 system, finding+emergent JSON을 user로 LLM 호출."""
    meta: dict[str, Any] = {"written": False, "by": writer.name}
    if not findings and not emergent:
        return "", meta
    if provider.name == "local":
        text = _fallback_narrative(findings, emergent)
        meta.update(
            written=bool(text),
            deterministic_fallback=True,
            reason="local provider has no LLM",
            chars=len(text),
        )
        return text, meta

    system = writer.body
    user_data = {
        "findings": [_finding_payload(f) for f in findings],
        "emergent": [_emergent_payload(e) for e in emergent],
    }
    user = json.dumps(user_data, ensure_ascii=False, indent=2)

    llm = provider.complete(system, user)
    if llm.error or not llm.text:
        meta["error"] = llm.error or "empty response"
        meta["llm_input_tokens"] = llm.input_tokens
        meta["llm_output_tokens"] = llm.output_tokens
        meta["llm_tokens_estimated"] = llm.estimated
        return "", meta

    text = _strip_code_fence(llm.text).strip()
    meta.update(
        written=bool(text),
        llm_input_tokens=llm.input_tokens,
        llm_output_tokens=llm.output_tokens,
        llm_tokens_estimated=llm.estimated,
        chars=len(text),
    )
    return text, meta


def _inject_narrative(report_body: str, narrative: str) -> str:
    """report.md 본문 맨 앞에 narrative 섹션을 prepend."""
    section = f"## 분석 요약\n\n{narrative}\n\n---\n\n"
    return section + report_body


def run_agentic_pipeline(
    bundle: Bundle,
    provider: BaseProvider,
    *,
    output_dir: Path,
) -> PipelineResult:
    output_dir = Path(output_dir)
    logger = EventLogger(
        output_dir,
        scenario_id=bundle.scenario_id,
        week=bundle.week,
        mode="agentic",
        provider=provider.name,
    )
    start = time.perf_counter()

    try:
        with logger.span("load_cards") as carry:
            cards = load_agent_cards()
            domain_cards = [c for c in cards if c.role == "expert"]
            reviewer = next((c for c in cards if c.role == "reviewer"), None)
            writer = next((c for c in cards if c.role == "writer"), None)
            carry["cards_total"] = len(cards)
            carry["domain_cards"] = [c.name for c in domain_cards]
            if not domain_cards:
                raise RuntimeError("agents/ 디렉토리에 도메인 expert 카드가 없습니다.")
            if reviewer is None or writer is None:
                raise RuntimeError("cost-reviewer 또는 solution-writer 카드가 없습니다.")

        with logger.span("detect") as carry:
            findings, _by_card = _collect_findings(domain_cards, bundle)
            carry["findings_count"] = len(findings)
            carry["patterns_found"] = sorted({f.pattern_id for f in findings})

        with logger.span("correlate") as carry:
            emergent = correlate(findings)
            carry["emergent_count"] = len(emergent)

        with logger.span("review", card=reviewer.name) as carry:
            reviewed, review_meta = _review_findings(reviewer, findings, provider)
            carry["llm_input_tokens"] = review_meta.get("llm_input_tokens", 0) or 0
            carry["llm_output_tokens"] = review_meta.get("llm_output_tokens", 0) or 0
            carry["reviewed"] = review_meta.get("reviewed", False)
            if review_meta.get("error"):
                carry["llm_error"] = review_meta["error"]

        with logger.span("write", card=writer.name) as carry:
            narrative, write_meta = _write_narrative(writer, reviewed, emergent, provider)
            carry["llm_input_tokens"] = write_meta.get("llm_input_tokens", 0) or 0
            carry["llm_output_tokens"] = write_meta.get("llm_output_tokens", 0) or 0
            carry["chars"] = write_meta.get("chars", 0)
            if write_meta.get("error"):
                carry["llm_error"] = write_meta["error"]

        # E1 Golden Set은 pure compute — provider 무관, 항상 실행.
        with logger.span("eval.golden") as carry:
            golden = golden_set_eval(bundle, reviewed)
            carry["precision"] = golden.get("precision")
            carry["recall"] = golden.get("recall")
            carry["f1"] = golden.get("f1")
            carry["missed"] = golden.get("missed")

        # E2 LLM-judge — provider가 local이면 evaluation.py 안에서 skip.
        with logger.span("eval.judge") as carry:
            judge = judge_narrative(narrative, reviewed, emergent, provider)
            if judge.get("skipped"):
                carry["skipped"] = True
                carry["reason"] = judge.get("reason")
            else:
                carry["factuality"] = judge.get("factuality")
                carry["clarity"] = judge.get("clarity")
                carry["completeness"] = judge.get("completeness")
                carry["llm_input_tokens"] = judge.get("llm_input_tokens", 0)
                carry["llm_output_tokens"] = judge.get("llm_output_tokens", 0)

        evaluation = {"golden": golden, "judge": judge, "run_id": logger.run_id}

        context = "\n".join(card.body for card in domain_cards)
        elapsed = round(time.perf_counter() - start, 6)
        llm_in = (
            (review_meta.get("llm_input_tokens", 0) or 0)
            + (write_meta.get("llm_input_tokens", 0) or 0)
            + (judge.get("llm_input_tokens", 0) or 0)
        )
        llm_out = (
            (review_meta.get("llm_output_tokens", 0) or 0)
            + (write_meta.get("llm_output_tokens", 0) or 0)
            + (judge.get("llm_output_tokens", 0) or 0)
        )
        llm_estimated = any(
            meta.get("llm_tokens_estimated", False)
            for meta in (review_meta, write_meta, judge)
        ) or provider.name == "local"
        warnings: list[str] = []
        if review_meta.get("error"):
            warnings.append(f"reviewer: {review_meta['error']}")
        if write_meta.get("error"):
            warnings.append(f"writer: {write_meta['error']}")
        if judge.get("skipped") and judge.get("reason") not in (
            None,
            "no narrative",
            "local provider has no LLM",
        ):
            warnings.append(f"judge: {judge.get('reason')}")

        agentic_result = AnalyzerResult(
            name="agentic",
            findings=reviewed,
            patterns_found=sorted({f.pattern_id for f in reviewed}),
            context_tokens_est=estimate_tokens(context),
            llm_input_tokens=llm_in,
            llm_output_tokens=llm_out,
            llm_tokens_estimated=llm_estimated,
            wall_clock_sec=elapsed,
            llm_usage={"review": review_meta, "write": write_meta, "judge": judge},
            warnings=warnings,
        )

        with logger.span("artifacts") as carry:
            artifacts = write_artifacts(
                output_dir,
                bundle,
                reviewed,
                baseline=None,
                multi=agentic_result,
                emergent=emergent,
                evaluation=evaluation,
            )
            carry["files"] = [p.name for p in artifacts.values()]

        # narrative가 있으면 report.md 상단에 섹션으로 끼움
        if narrative and "report" in artifacts:
            report_path = artifacts["report"]
            report_path.write_text(
                _inject_narrative(report_path.read_text(encoding="utf-8"), narrative),
                encoding="utf-8",
            )

        artifacts["events"] = logger.path

        logger.close(
            status="ok",
            findings_count=len(reviewed),
            llm_input_tokens=llm_in,
            llm_output_tokens=llm_out,
            wall_clock_sec=elapsed,
            golden_f1=golden.get("f1"),
        )

        return PipelineResult(
            bundle=bundle,
            selected=agentic_result,
            baseline=None,
            multi=agentic_result,
            emergent_findings=emergent,
            artifacts=artifacts,
        )
    except Exception as exc:
        logger.close(status="error", error=str(exc))
        raise
