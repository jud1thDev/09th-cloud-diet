# MA-005 분석 리포트 — Multi-account RI + SP + 계정 미통합

**시나리오**: MA-005 (GameNova · @m1cks)
**분석 일자**: 2026-05-25
**총 월 낭비 추정**: $5,585.35/mo
**패턴**: L3-032 + L3-033 + L3-034 (결합 시나리오)

---

## 분기 판단 (Orchestrator)

| 항목 | 값 |
|------|-----|
| 감지 | 결합 시나리오 (comp1_, comp2_, comp3_ prefix + "Component N/3" 주석) |
| 실행 | 멀티 에이전트 경로 (fan-out 3 → fan-in 1) |
| 도메인 분할 | comp1→ri_commitment, comp2→sp_coverage, comp3→account_governance |

진입점 `/solve-problem` 이 0단계에서 컴포넌트 3개를 감지하여 멀티 경로로 자동 분기.

---

## 발견한 문제 (3/3 패턴, Recall 100%)

### [P1] L3-032 — RI Family Mismatch (severity: critical, $1,401.60/mo)

**Root Cause**: m5.xlarge Standard RI 10개를 All Upfront로 선결제했으나, 워크로드가 c5.xlarge(×5) + r5.xlarge(×5)로 이동. Standard RI는 동일 instance family 내에서만 적용 → c5/r5에 미적용 → 온디맨드 이중 과금.

| 항목 | 값 |
|------|-----|
| 유휴 RI | m5.xlarge × 10 (All Upfront 1yr, 활용률 0%) |
| 정상 RI | m5.large × 5 (활용률 100%) |
| 온디맨드 과금 | $1,401.60/mo (c5+r5 10대, cost_report 확인값) |

**권장 해결**: EC2 RI Marketplace에서 10× m5.xlarge RI 매각 → Compute SP $2.73/hr (1yr no-upfront) 구매

---

### [P2] L3-033 — Compute SP Coverage 60% (severity: high, $1,200/mo)

**Root Cause**: Lambda 12개 + ECS Fargate 3서비스(12 tasks) + EC2 11대 SP 커버리지 60%. 전체 $7,500/mo 중 $3,000/mo 온디맨드 미보호.

| 항목 | 값 |
|------|-----|
| 전체 compute | ~$7,500/mo |
| SP 커버 | 60% ($4,500/mo) |
| 온디맨드 | 40% ($3,000/mo) |
| 절감 가능액 | $1,200/mo |

**권장 해결**: Compute SP $2.05/hr (1yr no-upfront) 추가 구매 → coverage 60%→75%

---

### [P3] L3-034 — AWS Organizations 미통합 (severity: critical, $2,983.75/mo)

**Root Cause**: 10개 계정 consolidated_billing=false. RI/SP 계정 간 공유 불가, enterprise volume discount 미달.

| 계정 | 월 지출 | RI % | SP % |
|------|---------|------|------|
| team-alpha | $1,800 | 25% | 0% |
| team-beta | $2,200 | 30% | 10% |
| team-gamma | $1,500 | 20% | 0% |
| team-delta | $1,200 | 0% | 15% |
| team-epsilon | $1,600 | 10% | 0% |
| dev-sandbox-1 | $800 | 0% | 0% |
| dev-sandbox-2 | $900 | 0% | 0% |
| staging | $2,000 | 15% | 5% |
| analytics | $1,700 | 20% | 0% |
| ml-platform | $1,300 | 0% | 10% |
| **합계** | **$15,000** | **평균 12%** | **평균 4%** |

**권장 해결**: Organizations 설정 → consolidated billing → RI Sharing → 중앙화 SP → enterprise tier

---

## Emergent Findings (멀티 에이전트 교차 발견)

> 컴포넌트별 전문가가 각자 출력한 cross_component_signals 를 synthesizer 가
> 교차 매칭하여 도출. 단일 에이전트의 단일 컨텍스트 구조에서는 산출되지 않는 인사이트.

### EF-001: Compound RI Stranding

**신호 매칭**: comp1 `idle_ri_sharing_opportunity` ↔ comp3 `ri_stranded_by_account_isolation`

comp1의 m5.xlarge RI 0% 활용은 단순 family mismatch가 아니다. consolidated_billing=false(comp3)로 인해 RI sharing이 차단됨으로써, org 내 다른 계정에서 m5.xlarge를 실행하더라도 이 RI를 공유할 수 없는 이중 손실 구조다.

**fix 순서 의미**: comp3(Organizations) 먼저 수정 → RI sharing 활성화 → m5.xlarge 사용 계정이 있으면 자동 흡수 → 없으면 Marketplace 매각

---

### EF-002: SP Fragmentation Spillover

**신호 매칭**: comp2 `sp_centralization_opportunity` ↔ comp3 `sp_fragmentation`

comp2 Compute SP는 per-account 스코프로 고정. comp3의 dev-sandbox-1/2($1,700/mo 순 온디맨드)에 SP가 spill-over되지 못한다. Organizations 통합 후 comp2 SP가 org-wide로 전환되면 **추가 구매 없이 ~$340/mo 추가 절감** 발생.

*이 $340/mo는 총계 $5,585.35에 미포함 — 실현 조건: comp3 fix 완료. cost_report authoritative 값 보존을 위해 별도 추적.*

---

### EF-003: Enterprise Volume Discount Threshold

**신호 매칭**: comp3 `enterprise_volume_discount_threshold` ↔ comp1 `on_demand_overspend_signal`

10개 계정 합산 $15,000/mo는 enterprise tier 기준 충족. 각 계정 단독(최대 $2,200)으로는 미달. consolidated billing 단일 조치로 volume discount가 자동 unlock.

*주의: 이 절감은 신규가 아니라 L3-034 $2,983.75 추정치에 이미 포함됨 (이중 계산 방지).*

---

## 절감 요약

| 우선순위 | 패턴 | 월 절감 | 실행 |
|---------|------|---------|------|
| 1 | L3-034 Organizations 통합 | $2,983.75 | 2시간 |
| 2 | L3-032 RI Marketplace 매각 + Compute SP | $1,401.60 | 1시간 |
| 3 | L3-033 SP coverage 추가 구매 | $1,200.00 | 30분 |
| (보너스) | EF-002 SP spill-over (추가 구매 없음, 총계 미포함) | $340.00 | Priority 1 완료 후 자동 |
| **합계** | | **$5,585.35/mo** | |

**연간 절감**: $67,024 (EF-002 보너스 포함 시 $71,104)

**절감액 중복 제거 (synthesizer 수행)**:
- comp1 전문가 추정 $1,987.22 → $1,401.60 정정 (forward savings $585.62와 sunk cost 중복 제거)
- comp2 전문가 추정 $600 → $1,200 정정 (cost_report SP gap 순 절감값 사용)
- comp3 $3,000 → $2,983.75 정정 (cost_report authoritative)
- 최종 합계: $1,401.60 + $1,200.00 + $2,983.75 = $5,585.35

---

## 단일 vs 멀티 에이전트 비교

> 측정값은 두 세션의 실제 `/cost` 기록 기반. 추론값과 구조적 추정은 명시적으로 구분 표기.

### 측정 비교 (실측)

| 메트릭 | 단일 에이전트 | 멀티 에이전트 |
|--------|--------------|--------------|
| 실행 방식 | 단일 컨텍스트 inline 분석 | 3 전문가 fan-out + synthesizer fan-in |
| Recall | 3/3 (100%) | 3/3 (100%) |
| 비용 (실측) | **$0.82** | **$2.10** (약 2.6×) |
| output 토큰 (실측) | 23.1k | 66.8k (약 2.9×) |
| cache read (실측) | 672.5k | 1.8m |
| API 시간 (실측) | 6m 28s | 19m 47s |
| Emergent findings | 0 (아래 주석) | 3 (EF-001/002/003) |
| 추가 절감 발견 | 없음 | EF-002 $340/mo |

### 측정 방법 및 한계 (정직성 명시)

- **비용·토큰·시간**: 두 세션의 `/cost` 화면 실측값. (단일 세션은 리팩토링 이전 순수 단일 구조에서 측정)
- **Emergent findings "단일 0"**: 단일 실행을 별도로 재현하여 "0개"임을 실험 증명한 것이 아니라, 단일 컨텍스트 구조상 cross_component_signals 교차 매칭 레이어가 존재하지 않으므로 **구조적으로 산출 불가**라는 판단. (실험적 0이 아닌 구조적 0)
- **토큰 배수**: hint.txt가 예측한 "멀티 ~15×"와 달리 실측 약 2.6×(비용 기준). 도메인별 chunk 분리로 각 전문가가 작은 컨텍스트만 처리하여 효율화된 것으로 해석. 단, 단일/멀티 세션의 cache 상태 등 조건이 완전히 동일하진 않으므로 정확한 통제 실험은 아님.

### 핵심 차이: Root Cause Ordering

- 단일 에이전트: 3가지 문제를 동등 병렬로 나열
- 멀티 에이전트: **L3-034(Organizations)가 root enabler** 라는 인과관계 발견 — 이를 먼저 수정해야 L3-032/L3-033 절감 효과가 증폭됨

### 회고

**멀티 에이전트가 추가 가치를 창출한 지점**:
1. 컨텍스트 격리 — 각 전문가가 자기 도메인만 분석하며 cross_component_signals 를 명시적으로 구조화
2. 신호 매칭 레이어 — synthesizer가 3개 전문가의 signals를 교차하여 emergent findings 추출
3. root cause ordering — 단일에서는 평면적이던 3개 문제가 멀티에서 governance → RI → SP 인과 순서로 정리됨

**한계 및 정직한 평가**:
- 단일 에이전트도 **recall 100%** 달성 — 이 시나리오는 main.tf 주석에 `Utilization: 0%` 등 답이 비교적 노출되어 있어 단일도 표면 발견에는 충분했음
- 멀티의 실질 우위는 recall이 아니라 **cross-component 인과 분석 + 추가 절감 $340 발굴 + fix 순서 도출**에 있음
- 본 비교는 완전 통제 실험이 아니므로(세션 조건 차이), 정밀 벤치마크는 향후 `--single`/`--multi` 동일 조건 재실행으로 보완 예정

**비용 대비 가치 판단 (토론 토픽 4번)**:
추가 비용 $1.28(= $2.10 − $0.82)로 emergent finding 3개 + 추가 절감 기회 $340/mo + fix 순서를 확보. 단발 분석 비용 대비 발굴 가치가 압도적이며, 결합 시나리오에서는 멀티가 정당화됨. 단순 단일 패턴(L1 등)에는 단일로 충분하므로, 난이도에 따라 경로를 분기하는 현재 orchestrator 설계가 합리적.