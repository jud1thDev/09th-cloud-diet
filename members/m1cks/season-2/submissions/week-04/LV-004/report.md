## RI & Spot Fleet 최적화 리포트

**시나리오**: LV-004  
**분석 기준일**: 2026-06-01  
**총 예상 월 절감액**: $2,128.90

---

## 1. RI Utilization — 저활용 RI 매각 권고

| RI ID | 인스턴스 타입 | 리전 | 활용률 | 미사용 시간 | 조치 | 복구 예상액 |
|---|---|---|---|---|---|---|
| ri-002 | r5.2xlarge | ap-northeast-2 | 23.1% | 553.7 h | **Sell (RI Marketplace)** | $106.04 |
| ri-003 | c5.2xlarge | us-east-1 | 45.8% | 390.2 h | **Sell (RI Marketplace)** | $50.41 |
| ri-005 | t3.large | us-west-2 | 31.2% | 495.4 h | **Sell (RI Marketplace)** | $15.66 |

### 판단 근거
- **ri-002 (23.1%)**: 활용률 < 50% → RI Marketplace 즉시 매각. 복구 예상액 $106.04.
- **ri-003 (45.8%)**: 활용률 < 50% → RI Marketplace 즉시 매각. 복구 예상액 $50.41.
- **ri-005 (31.2%)**: 활용률 < 50% → RI Marketplace 즉시 매각. 복구 예상액 $15.66.

> 세 RI 모두 활용률 50% 미만으로, 보유 유지 시 비용 대비 효익이 없음. RI Marketplace 매각을 통해 잔여 약정 가치를 회수해야 함.

---

## 2. RI Coverage — OD 과다 사용 구간 RI 구매 권고

| 인스턴스 타입 | 리전 | RI 커버리지 | OD 비율 | OD 시간 | 조치 | 월 절감 예상액 |
|---|---|---|---|---|---|---|
| c5.4xlarge | ap-northeast-2 | 0.0% | **100%** | 4,320 h | **RI 구매** | $1,116.29 |
| m5.4xlarge | us-east-1 | 0.0% | **100%** | 2,880 h | **RI 구매** | $840.50 |

### 판단 근거
- **c5.4xlarge (ap-northeast-2)**: OD 비율 100% > 60% 임계치. 4,320 OD 시간 전량 On-Demand 과금 중. 1년 표준 RI 전환 시 월 $1,116.29 절감.
- **m5.4xlarge (us-east-1)**: OD 비율 100% > 60% 임계치. 2,880 OD 시간 전량 On-Demand 과금 중. 1년 표준 RI 전환 시 월 $840.50 절감.

> 두 인스턴스 타입 모두 RI 커버리지 0%로, 월간 절감 가능액이 가장 큰 항목임. 즉시 1년 Standard RI 구매를 최우선으로 집행할 것.

---

## 3. Spot Interruption — 위험 구간 분석

### 3-1. AZ별 / 인스턴스 타입별 위험 분류

| 인스턴스 타입 | AZ | 스파이크 횟수 | 스파이크 가격 | OD 가격 | OD×0.85 임계 | 위험 레벨 |
|---|---|---|---|---|---|---|
| c5.2xlarge | ap-northeast-2a | 1 | $0.385 | $0.34 | $0.289 | **medium** |
| c5.2xlarge | ap-northeast-2c | 0 | — | $0.34 | $0.289 | **low** |
| m5.xlarge | ap-northeast-2a | 1 | $0.210 | $0.192 | $0.1632 | **medium** |

### 3-2. 위험 시간대 상세 (hourly_interruption_table 기반)

| 키 | 스파이크 횟수 | 요일 | 해석 |
|---|---|---|---|
| `hour=02\|c5.2xlarge\|ap-northeast-2a` | 1 | Wednesday | UTC 02시(KST 11시) 수요일 집중 위험 |
| `hour=14\|m5.xlarge\|ap-northeast-2a` | 1 | Tuesday | UTC 14시(KST 23시) 화요일 집중 위험 |

- **c5.2xlarge / ap-northeast-2a**: 스파이크 가격 $0.385 > OD×0.85($0.289). UTC 02시 수요일 인터럽션 추정.
- **m5.xlarge / ap-northeast-2a**: 스파이크 가격 $0.210 > OD×0.85($0.1632). UTC 14시 화요일 인터럽션 추정.
- **c5.2xlarge / ap-northeast-2c**: 스파이크 없음 → 저위험 구간.

---

## 4. Spot Fleet 다각화 권고

> ⚠️ 입력 데이터(interruption_patterns)에 존재하는 AZ·인스턴스 타입만 참조.

### 4-1. 회피 대상

**① c5.2xlarge / ap-northeast-2a**  
- 사유: price spike 1회 ≥ OD×0.85 ($0.289)  
- 대안 인스턴스: `c5a.2xlarge`, `c5n.2xlarge`, `c6i.2xlarge`  
- 대안 AZ: `ap-northeast-2c` (현재 스파이크 0회, low risk)

**② m5.xlarge / ap-northeast-2a**  
- 사유: price spike 1회 ≥ OD×0.85 ($0.1632)  
- 대안 인스턴스: `m5a.xlarge`, `m5n.xlarge`, `m6i.xlarge`  
- 대안 AZ: `ap-northeast-2c`로 분산 배치 권고 (입력 데이터 내 ap-northeast-2c는 c5.2xlarge 기준 low risk 확인)

### 4-2. 액션 플랜
1. Spot Fleet LaunchTemplate에서 `ap-northeast-2a` 단일 AZ 의존 제거
2. `c5.2xlarge`는 `ap-northeast-2c` + 대안 인스턴스 풀로 분산
3. `m5.xlarge`는 `m5a.xlarge` / `m6i.xlarge` 포함 멀티 인스턴스 풀 구성
4. `AllocationStrategy: capacityOptimized` 적용으로 실시간 용량 최적 AZ 자동 선택

---

## 5. 절감액 종합

| 카테고리 | 항목 | 예상액 |
|---|---|---|
| RI Utilization (매각 복구) | ri-002 r5.2xlarge | $106.04 |
| RI Utilization (매각 복구) | ri-003 c5.2xlarge | $50.41 |
| RI Utilization (매각 복구) | ri-005 t3.large | $15.66 |
| RI Coverage (월 절감) | c5.4xlarge ap-northeast-2 | $1,116.29 |
| RI Coverage (월 절감) | m5.4xlarge us-east-1 | $840.50 |
| **월 총 절감 합계** | | **$2,128.90** |

---

## 6. 우선순위 액션 플랜

| 우선순위 | 조치 | 예상 절감/복구 |
|---|---|---|
| P1 | m5.4xlarge(us-east-1) 1년 Standard RI 즉시 구매 | $840.50/월 |
| P1 | c5.4xlarge(ap-northeast-2) 1년 Standard RI 즉시 구매 | $1,116.29/월 |
| P2 | ri-002 r5.2xlarge RI Marketplace 매각 | $106.04 복구 |
| P2 | ri-003 c5.2xlarge RI Marketplace 매각 | $50.41 복구 |
| P3 | ri-005 t3.large RI Marketplace 매각 | $15.66 복구 |
| P2 | Spot Fleet: ap-northeast-2a 단일 AZ 의존 제거 + 멀티 인스턴스 풀 구성 | 인터럽션 위험 감소 |

---

## 7. 회고

- **OD 가격 단일값 한계**: 본 분석은 리전별 OD 가격을 단일 근사값으로 사용하여 실제 리전 간 가격 차이(예: ap-northeast-2 vs us-east-1)를 반영하지 못함. 절감액은 근사치임.
- **Spot 가격 이력 샘플 수 부족**: `hourly_interruption_table`의 각 키(hour=02|c5.2xlarge|ap-northeast-2a, hour=14|m5.xlarge|ap-northeast-2a)의 스파이크 횟수가 각 1회로, 통계적 신뢰도가 낮음. 더 긴 기간(최소 90일)의 이력 데이터를 수집하여 재분석 권고.