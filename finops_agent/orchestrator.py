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
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import detectors
from .analyzers import correlate
from .artifacts import write_artifacts
from .llm import BaseProvider, estimate_tokens
from .models import AnalyzerResult, Bundle, EmergentFinding, Finding, PipelineResult


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


def _review_findings(
    reviewer: AgentCard,
    findings: list[Finding],
    provider: BaseProvider,
) -> list[Finding]:
    """LLM 검수 placeholder. W2 3단계에서 본문을 채운다."""
    del reviewer, provider
    return findings


def _write_narrative(
    writer: AgentCard,
    findings: list[Finding],
    emergent: list[EmergentFinding],
    provider: BaseProvider,
) -> str:
    """report.md narrative placeholder. W2 5단계에서 LLM 호출을 끼운다."""
    del writer, findings, emergent, provider
    return ""


def run_agentic_pipeline(
    bundle: Bundle,
    provider: BaseProvider,
    *,
    output_dir: Path,
) -> PipelineResult:
    start = time.perf_counter()

    cards = load_agent_cards()
    domain_cards = [c for c in cards if c.role == "expert"]
    reviewer = next((c for c in cards if c.role == "reviewer"), None)
    writer = next((c for c in cards if c.role == "writer"), None)
    if not domain_cards:
        raise RuntimeError("agents/ 디렉토리에 도메인 expert 카드가 없습니다.")
    if reviewer is None or writer is None:
        raise RuntimeError("cost-reviewer 또는 solution-writer 카드가 없습니다.")

    findings, _by_card = _collect_findings(domain_cards, bundle)
    emergent = correlate(findings)
    reviewed = _review_findings(reviewer, findings, provider)
    _narrative = _write_narrative(writer, reviewed, emergent, provider)

    context = "\n".join(card.body for card in domain_cards)
    elapsed = round(time.perf_counter() - start, 6)
    agentic_result = AnalyzerResult(
        name="agentic",
        findings=reviewed,
        patterns_found=sorted({f.pattern_id for f in reviewed}),
        context_tokens_est=estimate_tokens(context),
        llm_input_tokens=0,
        llm_output_tokens=0,
        llm_tokens_estimated=True,
        wall_clock_sec=elapsed,
        llm_usage=None,
        warnings=[],
    )

    artifacts = write_artifacts(
        Path(output_dir),
        bundle,
        reviewed,
        baseline=None,
        multi=agentic_result,
        emergent=emergent,
    )
    return PipelineResult(
        bundle=bundle,
        selected=agentic_result,
        baseline=None,
        multi=agentic_result,
        emergent_findings=emergent,
        artifacts=artifacts,
    )
