### Week
3

### Scenario ID
XS-005

### Problem Identification
1. L3-025 — private subnet 경로가 중앙 NAT에 묶여 cross-AZ 전송비를 만든다.
- 문제 NAT: comp2_nat-gateway-r4cxxz
- `all_private`에 묶인 route table 3개: comp2_route-table-7rc8oa, comp2_route-table-9vg41t, comp2_route-table-bkmijw

2. L3-029 — analytics fleet의 S3 접근이 NAT 경로로 새고 있다.
- NAT + S3 요청 메트릭이 함께 잡히는 리소스 6개: comp1_instance-v5u2ym, comp1_instance-a4957a, comp1_instance-b552ti, comp1_instance-vgz8r0, comp1_instance-pntf0w, comp1_nat-gateway-o8ifim
- 같은 입력에는 direct S3 경로 리소스도 3개 있어, 일부 경로만 endpoint를 쓰고 일부는 NAT를 탄다.

### Root Cause
1. L3-025 root cause
- `comp2_nat-gateway-r4cxxz`의 `cross_az_bytes_mb_per_hr` 평균이 `100.0` MB/hr로 계속 0보다 크다.
- 문제 route table은 `associated_subnets = "all_private"`라 여러 AZ subnet을 한 경로에 몰아넣는다.
- 반대로 입력 안의 AZ-local NAT 후보 3개는 cross-AZ 평균이 `0.0`이라, 현재 낭비가 트래픽 양 자체가 아니라 경로 선택에서 생긴다는 점을 뒷받침한다.

2. L3-029 root cause
- 문제 리소스에서는 `nat_bytes_out_mb_per_hr`와 `s3_request_count_per_hr`가 함께 보이고, 대표 평균은 각각 `100.0` MB/hr와 `100.0` req/hr다.
- S3 접근을 private 경로로 흡수해야 할 endpoint 구성이 fleet 전체에 적용되지 않았다. Terraform provider는 `us-east-1`인데 기존 S3 endpoint service_name은 `ap-northeast-2`를 가리켜 현재 리전 경로를 보호하지 못한다.
- 그 결과 청구서는 NAT bytes로만 보이지만, 실제 payload는 S3 접근과 강하게 결합되어 있다.

3. Cross-service coupling
- 두 문제는 독립 낭비가 아니다. S3-heavy analytics traffic이 먼저 NAT를 통과하고, 그 같은 bytes가 중앙 NAT 경로 때문에 cross-AZ 전송비까지 만든다.
- 따라서 해결 순서는 `S3 Gateway Endpoint 정상화 → 남은 egress의 AZ-local NAT 정리`가 합리적이다.

### Proposed Solution
1. L3-025 조치
- `all_private`로 뭉친 문제 route table을 AZ-local 경로(`same_az_private`)로 전환한다.
- 이미 존재하는 AZ별 NAT 경로를 사용해 각 subnet이 같은 AZ의 NAT를 타도록 정리한다.
- 전환 후 `cross_az_bytes_mb_per_hr`가 0으로 내려가는지 확인한 뒤 중앙 경로 의존을 제거한다.

2. L3-029 조치
- 기존 S3 Gateway Endpoint를 현재 provider 리전에 맞는 service name으로 수정한다.
- 각 private route table마다 S3 endpoint association 리소스를 직접 참조로 추가한다.
- 적용 후 NAT bytes와 S3 direct bytes를 함께 확인해 우회 경로가 사라졌는지 검증한다.

### Estimated Monthly Savings (USD)
426.24

### 측정 데이터 (시즌 2 멀티 에이전트 비교)
측정 모드: `deterministic_local`. `deterministic_local`이면 토큰은 추정치이고 wall-clock은 detector 실행 시간 중심이다.

```json
{
  "scenario_id": "XS-005",
  "declared_patterns_from_prompt": [
    "L3-029",
    "L3-025"
  ],
  "true_recall_available": false,
  "coverage_basis": "README-declared scenario components; not blind recall",
  "measurement_mode": "deterministic_local",
  "wall_clock_scope": "detector runtime + optional summary calls",
  "single_agent": {
    "patterns_found": [
      "L3-025",
      "L3-029"
    ],
    "pattern_count": 2,
    "issue_count": 10,
    "declared_pattern_coverage": 1.0,
    "context_tokens_est": 6561,
    "llm_input_tokens": 315,
    "llm_output_tokens": 0,
    "llm_tokens_estimated": true,
    "wall_clock_sec": 0.000299,
    "warnings": []
  },
  "multi_agent": {
    "patterns_found": [
      "L3-025",
      "L3-029"
    ],
    "pattern_count": 2,
    "issue_count": 10,
    "declared_pattern_coverage": 1.0,
    "context_tokens_est": 6369,
    "llm_input_tokens": 443,
    "llm_output_tokens": 0,
    "llm_tokens_estimated": true,
    "wall_clock_sec": 0.000173,
    "warnings": []
  },
  "emergent_findings": [
    {
      "title": "S3 대량 트래픽이 중앙 NAT 경로에서 이중 과금된다",
      "detail": "Storage 관점은 NAT bytes의 payload가 S3임을 설명하고, Network 관점은 같은 bytes가 cross-AZ 경로까지 타고 있음을 설명한다.",
      "chain": "S3-heavy analytics traffic → centralized NAT → NAT processing + cross-AZ transfer",
      "recommendation": "먼저 S3 Gateway Endpoint로 대량 payload를 제거한 뒤, 남은 egress만 AZ-local NAT로 정리한다."
    }
  ]
}
```
