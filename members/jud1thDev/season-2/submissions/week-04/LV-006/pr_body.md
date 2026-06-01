## chore(infra): rightsizing recommendations [automated]

자동 분석 시각: LV-006 / Week 4

### 변경 요약

| Resource | Current | Recommended | Monthly Savings |
| --- | --- | --- | ---: |
| EC2 `prod-api-server-1` | m5.2xlarge | m5.large | $362.81 |
| EC2 `prod-worker-3` | c5.4xlarge | c5.2xlarge | $326.40 |
| EC2 `staging-web-1` | t3.2xlarge | t3.small | $218.40 |
| Lambda `data-processor` | 1024MB | 256MB | $34.20 |
| Lambda `image-resizer` | 3008MB | 768MB | $52.80 |
| Lambda `notification-sender` | 512MB | 128MB | $12.60 |
| EBS `vol-0abc123def456789a` | 미연결 | 삭제 (스냅샷 후) | $40.00 |
| EBS `vol-0def456789abc1230` | 미연결 | 삭제 (스냅샷 후) | $130.00 |
| ELB `my-idle-loadbalancer` | 0 req/day | 제거 | $18.25 |
| RDS `dev-legacy-database` | 0 connections | 스냅샷 후 정지 | $175.20 |

**총 추정 절감: $1370.66/월**

### Risk Assessment

- `prod-api-server-1` → 현재 타입: m5.2xlarge, 권장 타입: m5.large (rank=1, risk=2.1)
- `prod-worker-3` → 현재 타입: c5.4xlarge, 권장 타입: c5.2xlarge (rank=2, risk=1.2)
- `staging-web-1` → 현재 타입: t3.2xlarge, 권장 타입: t3.small (rank=1, risk=2.8)

### Cross-source agreement

- TA와 Compute Optimizer가 동일 EC2를 가리킨다 (cross-source agreement) — 중복 절감액을 더하지 말고 CO 권장 타입 + 절감 추정치 한 줄로 PR을 만든다. TA finding은 PR description의 보강 근거로만 인용한다.

### Rollback

- EC2 instance_type 변경은 `terraform apply` 후 instance 재시작 필요. 문제 발생 시 이전 타입으로 되돌리는 PR을 즉시 생성.
- EBS 삭제는 항상 스냅샷 먼저. 미연결 30일+ 기준이라 실제 사용 가능성 낮으나 30일 retention의 스냅샷을 만든 뒤 삭제.
- Lambda memory 변경은 즉시 적용. 콜드스타트 latency가 늘면 한 단계 위 값으로 재조정.

> 이 PR은 finops_agent가 자동 생성. Trusted Advisor + Compute Optimizer 응답을 cross-merge한 결과로, 동일 EC2에 두 신호가 일치하는 경우 PR description의 보강 근거로 인용된다.
