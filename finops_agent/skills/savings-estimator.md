---
name: savings-estimator
type: skill
used_by: [compute-expert, storage-expert, network-expert, database-expert, cost-reviewer]
---

# Savings Estimator

> `cost_report.summary`의 공개 절감액을 항목별로 어떻게 분배할지. 항목별 추정치를 직접 만들지 않고 공개값을 분배하는 게 원칙(재현성).

## 분배 규칙 (TBD)

- `cost_report.summary.estimated_monthly_savings`를 `Finding[]`의 `severity`·`pattern_id` 가중치로 분배
- 가중치 표 TBD — W2 3단계

## 금지 (TBD)

- 임의 단가 표(예: "Lambda GB-s = $0.0000166667")를 카드 안에서 곱하기 — 단가는 Live(W4) skill에서만 다룬다
- 항목별 추정치 합계가 공개 총액과 어긋남
