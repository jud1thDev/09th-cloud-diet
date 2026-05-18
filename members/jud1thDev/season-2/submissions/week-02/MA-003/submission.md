### Week
2

### Scenario ID
MA-003

### Problem Identification
1. L1-009 — ECR lifecycle 정책 부재
- lifecycle 정책이 없는 ECR repository 3개: comp2_ecr-repository-xps9mi, comp2_ecr-repository-1ixrd2, comp2_ecr-repository-adv88d
- ECR repository는 존재하지만 같은 컴포넌트에 lifecycle 정책 리소스가 없다. 정책 미적용 repo의 image_count 평균 370개로 이미지가 정리 없이 누적되고 있다.

2. L3-031 — 필수 비용 할당 태그 미준수
- 점검 대상 중 51개 리소스가 cost-center/team/environment/project 태그를 모두 충족하지 못한다.
- 유형별 분포: aws_db_instance 3개, aws_ecr_repository 5개, aws_eks_cluster 1개, aws_instance 35개, aws_lb 3개, aws_s3_bucket 4개

3. L3-038 — EKS 노드 플릿 과잉 프로비저닝
- m5.2xlarge로 고정된 노드 20개가 식별됐다.
- m5.2xlarge 노드가 다수 존재해 노드 플릿이 과도하게 크다. 해당 노드의 node_cpu_percent 평균 15.0%로 프로비저닝 대비 사용률이 매우 낮다.

### Root Cause
1. L1-009 root cause
- ECR repository와 lifecycle 정책이 1:1로 함께 정의되는 구조가 아니라, 일부 repo에만 정책이 붙었다.
- 정책이 없는 repo는 만료 기준이 없어 이미지가 무한히 누적된다.
- ECR repository는 존재하지만 같은 컴포넌트에 lifecycle 정책 리소스가 없다. 정책 미적용 repo의 image_count 평균 370개로 이미지가 정리 없이 누적되고 있다.

2. L3-031 root cause
- AWS Organizations Tag Policy/SCP로 필수 태그를 강제하지 않았고 provider default_tags도 없어, 태그 적용이 리소스 작성자 재량에 맡겨졌다.
- Terraform plan 단계에 태그 누락을 차단하는 정책 검증 게이트가 없어 비준수 리소스가 그대로 배포됐다.
- provider 블록에 default_tags가 없고, cost-center/team/environment/project 태그가 리소스별로 누락되어 있다. 미준수 리소스의 tag_coverage 평균이 0.0%로 사실상 태깅되지 않았다. unallocated_spend_ratio 평균 49.6%만큼 비용이 미할당 상태로 집계된다.

3. L3-038 root cause
- pod resource request가 실제 사용량을 크게 초과해, 낮은 부하에도 노드가 다수 필요한 것처럼 스케줄링된다.
- 그 결과 노드 인스턴스 타입이 피크 가정에 맞춰 m5.2xlarge로 고정됐다.
- m5.2xlarge 노드가 다수 존재해 노드 플릿이 과도하게 크다. 해당 노드의 node_cpu_percent 평균 15.0%로 프로비저닝 대비 사용률이 매우 낮다.

### Proposed Solution
1. L1-009 조치
- lifecycle 정책이 없는 ECR repository에 만료 정책을 추가해 오래된 이미지를 자동 정리한다.
- 신규 repo 누락을 막도록 repository와 lifecycle 정책을 함께 생성하는 구조로 정리한다.

2. L3-031 조치
- provider default_tags로 공통 태그 기준선을 깔고, 리소스별 cost-center/team/environment/project를 채운다.
- AWS Organizations Tag Policy로 필수 태그를 강제하고, CI 파이프라인에 태그 검증 게이트를 추가한다.

3. L3-038 조치
- 과잉 프로비저닝된 m5.2xlarge 노드를 m5.large로 다운그레이드한다.
- pod resource request를 실측 사용량 기준으로 재산정해 노드 수요 자체를 줄인다.

### Estimated Monthly Savings (USD)
8343.19

### 측정 데이터 (시즌 2 멀티 에이전트 비교)
측정 모드: `deterministic_local`. `deterministic_local`이면 토큰은 추정치이고 wall-clock은 detector 실행 시간 중심이다.

```json
{
  "scenario_id": "MA-003",
  "declared_patterns_from_prompt": [
    "L3-038",
    "L1-009",
    "L3-031"
  ],
  "true_recall_available": false,
  "coverage_basis": "README-declared scenario components; not blind recall",
  "measurement_mode": "deterministic_local",
  "wall_clock_scope": "detector runtime + optional summary calls",
  "single_agent": {
    "patterns_found": [
      "L1-009",
      "L3-031",
      "L3-038"
    ],
    "pattern_count": 3,
    "issue_count": 74,
    "declared_pattern_coverage": 1.0,
    "context_tokens_est": 14171,
    "llm_input_tokens": 2094,
    "llm_output_tokens": 0,
    "llm_tokens_estimated": true,
    "wall_clock_sec": 0.001319,
    "warnings": []
  },
  "multi_agent": {
    "patterns_found": [
      "L1-009",
      "L3-031",
      "L3-038"
    ],
    "pattern_count": 3,
    "issue_count": 74,
    "declared_pattern_coverage": 1.0,
    "context_tokens_est": 14133,
    "llm_input_tokens": 914,
    "llm_output_tokens": 0,
    "llm_tokens_estimated": true,
    "wall_clock_sec": 0.000983,
    "warnings": []
  },
  "emergent_findings": []
}
```
