"""파이프라인 단계 사이를 오가는 데이터 구조 정의.

이 파일에는 분석 로직이 전혀 없다. 각 단계(io → detectors → analyzers →
artifacts)가 주고받는 "데이터 그릇"만 dataclass로 모아 둔 곳이다. 처음 코드를
볼 때 이 파일을 먼저 훑으면 나머지 모듈이 어떤 값을 다루는지 그림이 잡힌다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Resource:
    """main.tf 안의 `resource "타입" "이름" { ... }` 블록 하나."""

    resource_type: str  # 예: "aws_db_instance"
    name: str  # Terraform 리소스 이름
    body: str  # 중괄호까지 포함한 블록 원문 (탐지기가 정규식으로 들여다본다)


@dataclass
class Component:
    """`# Component ...` 주석으로 구분된 리소스 묶음 한 덩어리."""

    index: int  # 몇 번째 컴포넌트인지 (1부터)
    total: int  # 전체 컴포넌트 개수
    pattern_id: str  # 주석에 적힌 seed 패턴 ID. 경계 분리에만 쓰고 탐지 힌트로는 쓰지 않는다
    text: str  # 이 컴포넌트 구간의 Terraform 원문
    resources: list[Resource] = field(default_factory=list)


@dataclass
class Bundle:
    """문제 폴더 하나를 읽어 분석에 필요한 모든 입력을 담은 객체.

    read_bundle()의 결과물이며, 이후 모든 분석 단계의 입력이 된다.
    """

    problem_dir: Path  # 문제 폴더 경로
    scenario_id: str  # 폴더 이름 = 시나리오 ID (예: "XS-005")
    week: int  # 주차 번호
    readme: str  # README.md 원문
    terraform: str  # main.tf 원문
    hint: str  # hint.txt 원문 (없으면 빈 문자열)
    cost_report: dict[str, Any]  # cost_report.json 파싱 결과
    metrics_summary: dict[str, Any]  # metrics.json을 요약 통계로 압축한 것
    components: list[Component]  # main.tf를 컴포넌트 단위로 쪼갠 목록
    pattern_ids: list[str]  # README에 선언된 패턴 ID 목록 (커버리지 계산 기준)
    level: str  # 문제 난이도 "L1"/"L2"/"L3" (패턴 ID에서 역산)
    available_files: list[str]  # 문제 폴더 안 파일 목록 (참고용)
    # Week 4 Live API 시나리오용. mock_responses/{name}.json → 파싱된 dict.
    # 정적 시나리오(W2/W3)는 빈 dict.
    live_responses: dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    """탐지기(detector)가 찾아낸 낭비 한 건."""

    pattern_id: str  # 어떤 패턴인지 (예: "L3-029")
    title: str  # 사람이 읽는 제목
    domain: str  # 도메인 분류 (network/storage/compute/database/governance)
    resource: str  # 문제가 된 리소스 이름
    issue_type: str  # 낭비 유형 (overprovisioned/unused/network/tagging/data)
    severity: str  # 심각도 (low/medium/high/critical)
    evidence: list[str]  # "왜 낭비라고 판단했는지" 근거 문장들
    recommendation: str  # 권장 조치
    estimated_savings: float  # 항목별 절감액 (현재는 0; 총액은 cost_report 공개값 사용)
    resource_type: str = ""  # 리소스 타입 (예: "aws_instance")


@dataclass
class EmergentFinding:
    """여러 finding을 가로질러 합성한 결합 원인(cross-service finding).

    한 영역만 봐서는 보이지 않고, 서비스 경계를 넘어야 드러나는 문제다.
    """

    title: str  # 결합 문제 제목
    detail: str  # 두 영역의 관찰이 어떻게 맞물리는지 설명
    chain: str  # 비용이 번지는 경로 (예: "S3 traffic → NAT → cross-AZ")
    recommendation: str  # 권장 해결 순서


@dataclass
class AnalyzerResult:
    """single 또는 multi 분석을 한 번 돌린 결과 + 측정값."""

    name: str  # "single" 또는 "multi"
    findings: list[Finding]  # 발견한 낭비 목록
    patterns_found: list[str]  # 발견한 패턴 ID 목록
    context_tokens_est: int  # 분석에 투입한 입력 컨텍스트 크기 추정값
    llm_input_tokens: int  # LLM 입력 토큰 (local 모드면 추정치)
    llm_output_tokens: int  # LLM 출력 토큰
    llm_tokens_estimated: bool  # 토큰이 추정치인지 여부 (True면 deterministic_local)
    wall_clock_sec: float  # 분석에 걸린 시간
    llm_usage: dict[str, Any] | None = None  # provider가 돌려준 원본 usage 정보
    warnings: list[str] = field(default_factory=list)  # LLM 호출 실패 등 경고


@dataclass
class PipelineResult:
    """파이프라인 한 번 실행의 최종 결과. run_pipeline()이 돌려준다."""

    bundle: Bundle  # 입력 번들
    selected: AnalyzerResult  # 산출물 생성에 실제로 쓴 분석 결과
    baseline: AnalyzerResult | None  # single 분석 결과 (안 돌렸으면 None)
    multi: AnalyzerResult | None  # multi 분석 결과 (안 돌렸으면 None)
    emergent_findings: list[EmergentFinding]  # cross-service 결합 원인 목록
    artifacts: dict[str, Path]  # 생성된 산출물 파일 경로 (이름 → 경로)
