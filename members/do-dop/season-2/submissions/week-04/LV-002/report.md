# LV-002 Spot Price Optimization — 분석 보고서

**생성 시각:** 2026-06-01T13:55:57  
**데이터 방식:** MOCK (실제 AWS API 응답을 모사한 재현 가능한 mock 데이터)  

---

## 1. 분석 개요

| 항목 | 값 |
|------|----|
| 대상 리전 | us-east-1, us-west-2, ap-northeast-2, ap-southeast-1, eu-west-1 |
| 인스턴스 타입 | m5.4xlarge, m5a.4xlarge, m5d.4xlarge, m4.4xlarge, m6i.4xlarge |
| 조회 기간 | 최근 30일 |
| 총 후보 수 | 6개 AZ×타입 조합 |
| 스코어링 가중치 | 절감=0.4, 안정성=0.3, 위험=0.3 |

---

## 2. 스코어링 알고리즘

```text
Score = 0.4 × savings_norm + 0.3 × stability_score − 0.3 × interruption_risk

savings_norm      = min(savings_pct / 100, 1.0)
stability_score   = max(0, 1 − stdev(spot_prices)/mean(spot_prices) × 5)
interruption_risk = min(1, spike_count / (n−1) × 10)
  spike 정의: 연속된 두 샘플 간 가격이 2배 이상 급등
```

**설계 근거:** AWS는 Spot 중단율을 직접 노출하지 않으므로, 본 구현에서는 가격 급등 빈도를 interruption risk의 proxy로 사용하였다. 이는 실제 중단율을 대체하는 근사 지표이며, 운영 적용 시 Spot Advisor, 실제 interruption 이벤트, SLA, checkpoint 비용과 함께 검증해야 한다.

---

## 3. Top 10 후보

| Rank | AZ | Type | OD($/hr) | Spot($/hr) | 절감% | 안정성 | 위험도 | Score | 월 절감 |
|------|-----|------|----------|-----------|-------|--------|--------|-------|--------|
| 1 | us-west-2a | m5.4xlarge | 0.7680 | 0.2446 | 68.2 | 0.8750 | 0.0000 | 0.5351 | $382.11 |
| 2 | us-east-1a | m5.4xlarge | 0.7680 | 0.2882 | 62.5 | 0.8332 | 0.0000 | 0.4999 | $350.25 |
| 3 | ap-northeast-2a | m5.4xlarge | 0.8560 | 0.3327 | 61.1 | 0.8247 | 0.0000 | 0.4919 | $381.97 |
| 4 | ap-northeast-2c | m5.4xlarge | 0.8560 | 0.2978 | 65.2 | 1.0000 | 0.5000 | 0.4108 | $407.49 |
| 5 | us-west-2b | m5.4xlarge | 0.7680 | 0.2689 | 65.0 | 1.0000 | 0.5000 | 0.4099 | $364.34 |
| 6 | us-east-1b | m5.4xlarge | 0.7680 | 0.3102 | 59.6 | 1.0000 | 0.5000 | 0.3884 | $334.19 |

---

## 4. 추천 Fleet 구성

- **전략:** diversified_spot_fleet
- **권장 비율:** Spot 80% + On-Demand 20%
- **인스턴스 패밀리:** m5 (1종)
- **분산 AZ:** ap-northeast-2a, us-east-1a, us-west-2a (3곳)

| AZ | Type | 절감% | 월 절감(USD) | 위험도 |
|----|------|-------|------------|--------|
| us-west-2a | m5.4xlarge | 68.2 | $382.11 | 0.0000 |
| us-east-1a | m5.4xlarge | 62.5 | $350.25 | 0.0000 |
| ap-northeast-2a | m5.4xlarge | 61.1 | $381.97 | 0.0000 |

---

## 5. 배치 전략 권장사항

1. **Spot 80% + On-Demand 20% 혼합 Fleet** — 비용 최적화와 최소 가용성 기준을 함께 만족
2. **3개 이상 인스턴스 패밀리 분산** — 특정 family capacity 부족이나 correlated interruption 완화
3. **2개 이상 AZ 분산** — 단일 AZ 용량 부족 및 가격 spike 리스크 완화
4. **interruption_risk ≥ 0.3 후보 제외** — 가격 급등 빈도가 높은 후보는 기본 추천에서 제외
5. **Job Checkpoint 필수** — Spot 중단 시 처음부터 재실행하지 않고 checkpoint부터 재시작
6. **최대 절감 후보:** us-west-2a / m5.4xlarge → 월 $382.11 절감 (68.2%)

---

## 6. 실제 AWS 환경 적용 시 변경 사항

현재 제출은 기본적으로 mock 데이터로도 실행 가능하도록 구성했다. 실제 AWS 환경에서는 같은 알고리즘을 유지하고 collector만 아래 API로 교체할 수 있다.

```python
get_on_demand_price_aws()      # pricing:GetProducts
get_spot_price_history_aws()  # ec2:DescribeSpotPriceHistory
```

필요 IAM 권한:

```text
pricing:GetProducts
ec2:DescribeSpotPriceHistory
```

실제 계정에 Spot 기반 배치 워크로드가 없는 경우에도, 본 구현은 Live API형 입력 구조와 최적화 알고리즘을 검증하는 PoC로 사용할 수 있다.
