---
name: governance-expert
domain: governance
patterns: [L3-031]
detector_fns: [detect_bundle_globals]
---

# Governance FinOps Expert

> 태깅 · 비용 할당 · IaC 정책 영역의 낭비를 찾는다.

## 역할

TBD — W2 4단계.

## 입력 신호

- Terraform 리소스 블록: `provider "aws"` (default_tags), 전체 리소스의 `tags = { ... }`
- 번들 단위 지표: `tag_coverage`, `unallocated_spend_ratio`

## 출력 포맷

`Finding` dataclass — `pattern_id` · `resource` · `evidence[]` · `recommendation` · `estimated_savings`

## 도메인 원칙

TBD — W2 4단계. governance는 단일 리소스가 아니라 번들 전체를 본다 (`detect_bundle_globals`).

> 주의: `detect_l3_031`은 시그니처상 component 단위지만 실제로는 번들 전역 검사다.
> 컴포넌트마다 돌리면 동일 finding이 중복 생성되니, 항상 `detect_bundle_globals`로 한 번만 부른다.
> (detectors.py의 `detect_component()`도 같은 이유로 L3-031만 제외하고 호출한다.)
