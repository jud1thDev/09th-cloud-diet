---
name: cost-reviewer
role: reviewer
inputs: [Finding, EmergentFinding]
outputs: [Finding]
llm_calls: 1
retry: 1
---

# Cost Finding Reviewer

> 도메인 전문가가 모은 `Finding[]`을 검증한다. 근거가 약하면 `confidence: low`를 붙이고, 명백히 잘못된 항목은 드롭한다.

## 역할

TBD — W2 3단계에서 storage-expert와 함께 본문 확정.

## 입력 신호

- `Finding[]` (도메인 전문가 fan-out 결과 합집합)
- `EmergentFinding[]` (analyzers.correlate 결과)
- bundle.readme, bundle.cost_report.summary (검증 컨텍스트)

## 검증 체크리스트 (TBD)

- evidence가 수치·리소스 이름·지표명을 포함하는가
- estimated_savings가 cost_report 공개값 분배 규칙(`skills/savings-estimator.md`)을 따르는가
- 같은 리소스에 모순된 권장이 없는가 (예: "Multi-AZ 유지" + "Single-AZ로 전환")

## 출력 포맷

`Finding` dataclass — 입력 그대로 + 옵션 필드:
- `confidence: "low" | "high"` (없으면 high로 간주)
- `review_notes: str` (의심 사유)

## 도메인 원칙

TBD.
