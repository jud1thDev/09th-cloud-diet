# Week 2 Multi-Agent Report

## Comparison Summary

```json
{
  "single_agent": {
    "recall": 0.333,
    "input_tokens": 2435,
    "output_tokens": 1189,
    "wall_clock_sec": 29.68
  },
  "multi_agent": {
    "recall": 1.0,
    "input_tokens": 1779,
    "output_tokens": 334,
    "wall_clock_sec": 12.57,
    "agent_count": 3
  },
  "framework": "lightweight rule-based analyzer",
  "notes": "Single-agent는 필수 3개 패턴 중 1개를 감지했고, multi-agent는 3개를 감지함. Multi-agent는 cross-service finding 도출 목적."
}
```

## Baseline Result

- Single-agent issues: 3
- Estimated monthly savings: $1,632.00
- Confidence score: 85%
- Single-agent LLM calls: 1
- Single-agent estimated tokens: 3,624
- Single-agent wall-clock: 29.68s
- Single-agent recall estimate: 1/3 (33.3%)

## Multi-Agent Result

- Detected domains: lambda, dynamodb, governance
- Rule-based domain issues: 7
- Cross-domain query exchanges: 2
- Cross-service findings: 1
- Extra LLM calls: 1
- Extra estimated tokens: 2,113
- Multi-agent wall-clock: 12.57s
- Total token ratio vs single: 1.58x
- Token delta: +2,113
- Multi-agent recall estimate: 3/3 (100.0%)

## Recall Estimate

- Ground truth patterns: L1-010, L2-014, L2-015
- Single found patterns: L1-010
- Multi found patterns: L1-010, L2-014, L2-015
- Single recall: 1/3 (33.3%)
- Multi recall: 3/3 (100.0%)
- Basis: scenario pattern IDs from cost_report._fusion_components/readme/hint

## Issues Found

- comp1_lambda-function-xoq9qq, comp1_lambda-function-0n5puy, comp1_lambda-function-j5dyhj (overprovisioned, high): $750.00/month
- comp2_lambda-function-w8lsz8, comp2_lambda-function-bybdc5 (overprovisioned, high): $360.00/month
- comp3_dynamodb-table-bh7jai (overprovisioned, medium): $522.00/month

## Domain Analyzer Findings

### lambda
- `lambda_memory_overprovisioned` on `comp1_lambda-function-xoq9qq`: 설정 3008MB 대비 P95 사용률 3.3%
- `lambda_memory_overprovisioned` on `comp1_lambda-function-0n5puy`: 설정 3008MB 대비 P95 사용률 3.3%
- `lambda_memory_overprovisioned` on `comp1_lambda-function-j5dyhj`: 설정 3008MB 대비 P95 사용률 3.3%
- `excessive_timeout` on `comp2_lambda-function-w8lsz8`: P99 6303ms 대비 timeout 900s - 에러 시 최대 900s 과금
- `excessive_timeout` on `comp2_lambda-function-bybdc5`: P99 4924ms 대비 timeout 900s - 에러 시 최대 900s 과금

### dynamodb
- `dynamodb_provisioned_overallocated` on `comp3_dynamodb-table-bh7jai`: Provisioned capacity 대비 사용량이 낮고 throttling 신호가 약함

### governance
- `terraform_default_tags_missing` on `aws_provider`: Terraform provider default_tags가 없어 신규 리소스 태깅 누락 위험이 있음

## Cross-Domain Query Loop

- `lambda` -> `dynamodb` (answered)
  - Question: Lambda duration/error/burst 패턴이 DynamoDB provisioned capacity 적정성에 영향을 주는지 확인 필요
  - Reason: MA-001 유형의 Lambda-DynamoDB 결합 낭비 판단
  - Answer: dynamodb_provisioned_overallocated/comp3_dynamodb-table-bh7jai: Provisioned capacity 대비 사용량이 낮고 throttling 신호가 약함
- `dynamodb` -> `lambda` (answered)
  - Question: comp3_dynamodb-table-bh7jai 접근 Lambda 호출이 steady인지 burst인지 확인 필요
  - Reason: DynamoDB provisioned 유지와 on-demand 전환 중 어느 쪽이 적합한지 판단
  - Answer: lambda_memory_overprovisioned/comp1_lambda-function-xoq9qq: 설정 3008MB 대비 P95 사용률 3.3% ; lambda_memory_overprovisioned/comp1_lambda-function-0n5puy: 설정 3008MB 대비 P95 사용률 3.3% ; lambda_memory_overprovisioned/comp1_lambda-function-j5dyhj: 설정 3008MB 대비 P95 사용률 3.3% ; excessive_timeout/comp2_lambda-function-w8lsz8: P99 6303ms 대비 timeout 900s - 에러 시 최대 900s 과금 ; excessive_timeout/comp2_lambda-function-bybdc5: P99 4924ms 대비 timeout 900s - 에러 시 최대 900s 과금

## Emergent Findings

Lambda의 과도한 timeout 설정(900초)이 DynamoDB provisioned capacity 낭비를 증폭시키는 결합 낭비가 발견되었습니다. Lambda 에러 시 최대 900초 과금과 함께 DynamoDB 접근 패턴이 왜곡되어 실제 필요량 대비 과도한 capacity가 할당되고 있습니다.

### api_gateway_lambda_dynamodb_cascade_amplification

- Scenario: API Gateway -> Lambda -> DynamoDB cascade amplification
- Severity: high
- Services: Lambda, DynamoDB
- Domains: lambda, dynamodb
- Chain: Lambda → DynamoDB
- Root cause: Lambda의 과도한 timeout 설정이 DynamoDB 접근 패턴을 왜곡시켜 provisioned capacity 낭비를 증폭
- Amplification: Lambda 에러 시 900초 동안 과금되면서 DynamoDB 접근 패턴이 불규칙해지고, 이로 인해 provisioned capacity가 실제 필요량보다 과도하게 할당됨
- Recommendation: Lambda timeout을 11초/10초로 축소하고 DLQ 설정 후, DynamoDB를 PAY_PER_REQUEST로 전환하여 burst 패턴에 맞는 과금 모델 적용
- Links:
  - Lambda -> DynamoDB: excessive timeout extends retry-driven compute cost and amplifies provisioned capacity waste
- Evidence:
  - lambda: comp2_lambda-function-w8lsz8과 comp2_lambda-function-bybdc5에서 timeout 900s 대비 P99 6303ms/4924ms로 에러 시 최대 900s 과금
  - dynamodb: comp3_dynamodb-table-bh7jai에서 provisioned capacity 대비 사용량이 낮고 throttling 신호가 약함

## Measurement Notes

- Token counts are estimated from prompt/response text length when provider usage metadata is unavailable.
- Wall-clock is measured locally around the single-agent and multi-agent phases.
- Recall is estimated by mapping detected issue types/resources to scenario pattern IDs when ground-truth pattern metadata is available.
