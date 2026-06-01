# XS-003 분석 리포트 — ECS 다운스케일 후 살아남은 인프라 (PulseAI)

**분석 일자**: 2026-05-25 · **도구**: WalletBuffer (Claude Code subagent)
**분기 판단**: 감지 결합(comp 3개, L2-016/L1-005/L2-017) / 단일(`--single`) baseline + 멀티(`--multi`) 비교

---

## 1. 발견 문제 요약 (recall 3/3)

| # | 리소스 | 패턴 | 심각도 | 월 절감 |
|---|--------|------|--------|---------|
| 1 | 10× ECS Fargate 서비스 (comp1) | L2-016 | critical | $1,050.00 |
| 2 | autoscaling-group-wsdeme (comp3) | L2-017 | high | $420.48 |
| 3 | lb-pzjz8f (comp2) | L1-005 | medium | $16.43 |
| 4 | lb-xz7ylo (comp2) | L1-005 | medium | $16.43 |
| **합계** | | | | **$1,503.33/mo** |

cost_report avg_monthly_waste: $1,480.87/mo (오차 1.5%)

---

## 2. 컴포넌트별 상세 분석

### Component 1/3 — ECS Fargate 과잉 프로비저닝 (L2-016)

**문제**: 10개 ECS 서비스가 Black Friday 사양(4vCPU/8GB × desired_count=5 = 50 tasks)을 유지. 동일 클러스터 정상 서비스(ecs-service-9i0gu6, g1m7ei)는 이미 1vCPU/2GB로 올바르게 설정됨.

**메트릭** (comp1_ecs-service-nn78pg 대표): mean_cpu 10.98%, p95_cpu 20.77%, p99_cpu 22.34%, mean_utilized_vcpu 0.44vCPU (4vCPU 중 11% 사용)

**권장**: `cpu="4096"→"1024"`, `memory="8192"→"2048"` (10개 task definition 전체)

**절감**: cost_report pricing_note (~$1,400/mo combined ECS+Fargate의 75%) → **$1,050/mo**

### Component 2/3 — Idle ALB (L1-005)

**문제**: Black Friday용 수동 생성 ALB 2개가 이벤트 종료 후 미삭제.

| ALB | request_count (30일) | is_problem |
|-----|---------------------|------------|
| lb-pzjz8f | 0 (720 datapoints 전부 0) | true |
| lb-xz7ylo | 0 (720 datapoints 전부 0) | true |
| lb-mhvy4k | 트래픽 있음 | false (유지) |

**절감**: 2 × \$0.0225/hr × 730hr = **\$32.85/mo**

### Component 3/3 — ASG 과잉 프로비저닝 (L2-017)

**문제**: autoscaling-group-wsdeme의 max_size=20이 Black Friday 용량에서 미복구. target_value=60%가 과도한 scale-out 유발.

**메트릭**: mean_instance_count 8.44 (baseline ~5), p95 15.4, 초과 ~3개 (m5.xlarge \$0.192/hr), 범위 0.8~16.66

**권장**: `max_size=20→8`, `target_value=60→70`

**절감**: 3 × \$0.192/hr × 730hr = **\$420.48/mo**

---

## 3. 교차 컴포넌트 발견 (Emergent Finding)

### "Post-Black-Friday Infrastructure Cleanup Failure"

**단일 에이전트가 놓치기 쉬운 패턴**: 세 컴포넌트가 동일한 근본 원인을 공유.

| 컴포넌트 | 신호 | 증거 |
|---------|------|------|
| comp1 (ECS) | 이벤트 후 task spec 미복구 | 정상 서비스(9i0gu6, g1m7ei)는 1vCPU/2GB — 이벤트 서비스만 4vCPU/8GB 잔존 |
| comp2 (ALB) | 이벤트 후 수동 생성 ALB 미삭제 | 30일 전 기간 request_count=0, lb-mhvy4k는 정상 |
| comp3 (ASG) | 이벤트 후 max_size 미복구 | max_size=20 유지, 평균 8.44 인스턴스 |

**근본 원인**: 이벤트 스케일링 변경을 IaC가 아닌 수동/임시 runbook으로 처리 → 롤백 프로세스 부재. TTL 태깅·IaC drift 탐지·이벤트 후 정리 자동화 없음.

**권장**:
1. 이벤트 스케일링은 Terraform revert PR로 관리 (시작 시 PR 생성, 종료 시 merge)
2. 수동 생성 리소스에 `finops:auto-cleanup-after=<date>` 태그 + Lambda/EventBridge 강제 삭제
3. AWS Config 규칙: `env=prod`에서 ECS task CPU > 2vCPU이고 `active-event` 태그 없으면 알림
4. 월간 ASG max_size 감사: max_size > 2 × 30일 p95 인스턴스 수면 플래그

> 이 emergent finding의 직접 절감은 **\$0** (독립 리소스, 절감액 합산 불가). 가치는 "추가 절감"이 아니라 **공통 원인 도출 + 재발 방지**에 있음.

---

## 4. 단일 vs 멀티 에이전트 비교

| 항목 | 단일 (`--single`) | 멀티 (`--multi`) |
|------|------------------|------------------|
| 파이프라인 | terraform-analyzer → finops-analyst → answer-verifier | terraform-analyzer(chunk) → compute·network 병렬 fan-out → synthesizer fan-in → verifier |
| recall | 3/3 | 3/3 |
| 발견 이슈 | 3 (개별 패턴) | 4 (+ emergent) |
| emergent finding | **0** | **1** (cleanup failure) |
| 총 절감 | \$1,503.33 | \$1,503.33 |
| 비용 (`/cost`) | \$1.57 | \$1.39 |
| wall-clock (`/cost`) | 18m 51s | 14m 9s |
| output tokens (`/cost`) | ~43.7k | ~40.3k |
| agent 수 (종류) | 3 | 5 |

### 핵심 결론
- **recall 동급(3/3)** — 세 패턴이 컴포넌트별 독립 탐지 가능하므로 도메인 전문가만으로 양쪽 누락 없음.
- **멀티만 emergent finding 도출** — 공통 root cause는 cross-component 신호 교차가 필요해 단일 컨텍스트에서 구조적으로 미도출. 이 시나리오에서 멀티의 핵심 가치.
- 절감액 동일 — 멀티는 "절감을 더 찾는" 도구가 아니라 "원인을 묶는" 도구.

### 측정 정직성 (보너스 항목) — 비교의 한계
위 비용/토큰은 **직접 비교에 한계가 있다**. 정직하게 기록:
1. **세션 오염**: 단일 baseline은 specialist 추가·파일 이동·검증 등 리팩토링 작업이 혼재된 세션에서 측정. 멀티는 깨끗한 0점 세션. \$1.57 vs \$1.39 차이를 구조 차이로 귀속 불가.
2. **방향 역전**: 일반적으로 멀티가 컨텍스트 재로딩으로 더 비싸야 정상(2주차: 단일 \$0.82 < 멀티 \$2.10). 이번 역전 자체가 측정 오염 신호.
3. **cache 미분리**: `/cost`가 cache를 input과 분리하지 못해 순수 input_tokens 집계 불가.
4. **개선 방향**: 정밀 측정을 위해 **Agent SDK 기반 측정 하니스**를 추후 별도 마련 예정 (세션 격리 + subagent별 usage 분리로 cache 영향 없이 정확 계측 → 동일 조건 재측정).

---

## 5. 적용 변경사항 (main_optimized.tf)

1. **10× ECS task definition**: `cpu="4096"→"1024"`, `memory="8192"→"2048"` (+ container_definitions 동일)
2. **lb-pzjz8f** 리소스 블록 삭제
3. **lb-xz7ylo** 리소스 블록 삭제
4. **autoscaling-group-wsdeme**: `max_size=20→8`, `target_value=60→70`

원본 837줄 → 최적화 813줄 (−24줄, ALB 2개 블록 제거)

---

## 6. 권장 조치 순서

1. **(우선)** ECS Fargate 10개 rightsizing → `terraform apply` (무중단 롤링) — \$1,050/mo
2. **(2순위)** ASG wsdeme target_value 70% — \$420.48/mo
3. **(3순위)** idle ALB 2개 삭제 — \$32.85/mo

**총 절감**: \$1,503.33/mo · **연간**: ~\$18,039.96
