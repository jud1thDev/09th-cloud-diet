### Week
4

### Scenario ID
LV-006

### Problem Identification
1. LV-006-CO-EC2: Compute Optimizer: EC2 rightsizing (prod-api-server-1, prod-worker-3, staging-web-1)

2. LV-006-CO-LAMBDA: Compute Optimizer: Lambda 메모리 rightsizing (data-processor, image-resizer, notification-sender)

3. LV-006-TA-EBS: Trusted Advisor: 미연결 EBS 볼륨 (vol-0abc123def456789a, vol-0def456789abc1230)

4. LV-006-TA-EC2: Trusted Advisor: 저활용 EC2 (i-0123456789abcdef0)

5. LV-006-TA-ELB: Trusted Advisor: idle Load Balancer (my-idle-loadbalancer)

6. LV-006-TA-RDS: Trusted Advisor: idle RDS (dev-legacy-database)

### Root Cause
1. LV-006-CO-EC2 root cause
- Compute Optimizer는 최근 14일 CloudWatch 메트릭을 기반으로 OVER_PROVISIONED 인스턴스를 식별한다.
- 대상 인스턴스 3개의 CPU MAX가 모두 권장 사이즈에서도 80% 미만으로 유지될 것으로 예측된다.
- 결정 로직: rank=1 옵션 중 `performanceRisk<3.0`인 것을 채택하고, rank=1이 위험하면 rank=2로 폴백한다.

2. LV-006-CO-LAMBDA root cause
- Compute Optimizer Lambda recommender는 호출별 메모리 활용률을 14일 관찰한다.
- 대상 함수 3개는 모두 Memory MAX가 현재 할당의 50% 미만이라 OVER_PROVISIONED로 분류된다.
- rank=1 권장 메모리만 채택. Duration 변화는 power-tuning이 필요한 별개 의사결정이라 본 권장에서는 다루지 않는다.

3. LV-006-TA-EBS root cause
- Trusted Advisor `Cost Optimizing` 카테고리가 미연결 EBS로 플래그한 리소스 2개.
- 판단 근거(metadata): ap-northeast-2 / vol-0abc123def456789a / gp3 / 500 GiB
- TA는 청구서 단가 기반의 보수적 추정이라 실제 절감 폭은 CO 권장 또는 자체 단가표로 한 번 더 검증해야 한다.

4. LV-006-TA-EC2 root cause
- Trusted Advisor `Cost Optimizing` 카테고리가 저활용 EC2로 플래그한 리소스 1개.
- 판단 근거(metadata): ap-northeast-2 / i-0123456789abcdef0 / m5.2xlarge / CPU avg 2.1% over 14 days
- TA는 청구서 단가 기반의 보수적 추정이라 실제 절감 폭은 CO 권장 또는 자체 단가표로 한 번 더 검증해야 한다.

5. LV-006-TA-ELB root cause
- Trusted Advisor `Cost Optimizing` 카테고리가 idle ELB로 플래그한 리소스 1개.
- 판단 근거(metadata): ap-northeast-2 / my-idle-loadbalancer / Classic Load Balancer / No active back-end instances
- TA는 청구서 단가 기반의 보수적 추정이라 실제 절감 폭은 CO 권장 또는 자체 단가표로 한 번 더 검증해야 한다.

6. LV-006-TA-RDS root cause
- Trusted Advisor `Cost Optimizing` 카테고리가 idle RDS로 플래그한 리소스 1개.
- 판단 근거(metadata): ap-northeast-2 / dev-legacy-database / db.r5.large / 0 connections over 14 days
- TA는 청구서 단가 기반의 보수적 추정이라 실제 절감 폭은 CO 권장 또는 자체 단가표로 한 번 더 검증해야 한다.

Cross-source agreement (TA × CO)
- Trusted Advisor의 저활용 EC2 finding과 Compute Optimizer의 OVER_PROVISIONED 권장이 동일 인스턴스 ID에서 만난다.
- 두 신호가 일치하면 권장 적용 위험도가 낮다고 본다. 단 절감액은 두 번 더하지 않고 CO 추정치로 일원화한다 — TA의 월 비용 표시는 인스턴스 단가, CO는 권장 타입과의 차액이라 성격이 다르기 때문이다.

### Proposed Solution
1. LV-006-CO-EC2: Compute Optimizer가 권장한 인스턴스 타입(performanceRisk<3.0)으로 Terraform PR을 생성한다.

2. LV-006-CO-LAMBDA: Compute Optimizer가 권장한 memory_size로 aws_lambda_function 리소스를 PR로 갱신한다.

3. LV-006-TA-EBS: 30일 이상 미연결된 EBS 볼륨은 스냅샷 후 삭제한다.

4. LV-006-TA-EC2: CPU 평균 5% 미만 인스턴스를 Compute Optimizer 권장 타입으로 다운사이즈한다.

5. LV-006-TA-ELB: 트래픽이 없는 Load Balancer를 제거하거나 backend를 재연결한다.

6. LV-006-TA-RDS: 연결이 없는 RDS는 스냅샷 후 정지/삭제한다.

### Estimated Monthly Savings (USD)
1370.66

### 측정 데이터 (시즌 2 멀티 에이전트 비교)
측정 모드: `deterministic_local`. `deterministic_local`이면 토큰은 추정치이고 wall-clock은 detector 실행 시간 중심이다.

```json
{
  "scenario_id": "LV-006",
  "declared_patterns_from_prompt": [
    "LV-006"
  ],
  "true_recall_available": false,
  "coverage_basis": "README-declared scenario components; not blind recall",
  "measurement_mode": "deterministic_local",
  "wall_clock_scope": "detector runtime + optional summary calls",
  "single_agent": null,
  "multi_agent": {
    "patterns_found": [
      "LV-006-CO-EC2",
      "LV-006-CO-LAMBDA",
      "LV-006-TA-EBS",
      "LV-006-TA-EC2",
      "LV-006-TA-ELB",
      "LV-006-TA-RDS"
    ],
    "pattern_count": 6,
    "issue_count": 11,
    "declared_pattern_coverage": 1.0,
    "context_tokens_est": 678,
    "llm_input_tokens": 0,
    "llm_output_tokens": 0,
    "llm_tokens_estimated": true,
    "wall_clock_sec": 0.000853,
    "warnings": []
  },
  "emergent_findings": [
    {
      "title": "TA와 Compute Optimizer가 동일 EC2를 가리킨다 (cross-source agreement)",
      "detail": "Trusted Advisor가 CPU 평균 미달로 표시한 EC2가 Compute Optimizer의 OVER_PROVISIONED 권장과 인스턴스 ID 수준에서 일치한다. 두 독립 신호가 같은 결론을 내릴 때 PR 자동 적용 위험도는 낮아진다.",
      "chain": "TA Cost Optimizing check → CO 14d metric analysis → 동일 인스턴스 ID 매칭 → 단일 권장",
      "recommendation": "중복 절감액을 더하지 말고 CO 권장 타입 + 절감 추정치 한 줄로 PR을 만든다. TA finding은 PR description의 보강 근거로만 인용한다."
    }
  ]
}
```
