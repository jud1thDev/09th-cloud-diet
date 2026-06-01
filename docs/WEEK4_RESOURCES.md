# Week 4 — Live 환경 분석 학습 자료

> 이번 주차 목표: 정적 `main.tf` + `cost_report.json` 분석을 **졸업**하고, **실시간 AWS API**(boto3 / Cost Explorer / CUR 2.0 / Pricing API)를 호출해야만 풀리는 시나리오로 확장.
> 본인 도구에 **AWS SDK 연동 모듈 + mock 모드**를 추가하는 게 산출물.

---

## 🎯 이번 주차에서 가져가야 할 것

1. **Cost Explorer API** — `GetCostAndUsage` (HOURLY granularity, GroupBy SERVICE/USAGE_TYPE)로 시간별 비용 드릴다운
2. **Cost Anomaly Detection API** — `GetAnomalies`로 이상 탐지 결과를 받아 자동 root-cause 분석
3. **CUR 2.0 + Athena** — daily aggregate를 넘어 hourly·tag·RI/SP allocation을 SQL로 질의
4. **실시간 단가** — Price List API(`GetProducts`) + `DescribeSpotPriceHistory`로 정적 catalog 대신 live 단가
5. **mock 모드 패턴** — `if mock_mode: json.load(mock_file) else: client.call(...)` 로 AWS 계정 없이도 동일 파이프라인 실행

---

## 🔴 필수 (이번 주차 토론 베이스)

### 1. [GetCostAndUsage — boto3 reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce/client/get_cost_and_usage.html) · [API Reference](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostAndUsage.html)
**AWS 공식 / 읽기 20분**
Granularity를 `HOURLY`로 두고 `GroupBy=[SERVICE, USAGE_TYPE]` 조합으로 spike line item을 분해하는 핵심 API. `NextPageToken` 페이지네이션, HOURLY는 요청당 최대 1일 — 이 제약이 LV-001 구현의 뼈대. (리소스 단위는 [`GetCostAndUsageWithResources`](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostAndUsageWithResources.html), EC2는 hourly opt-in)

### 2. [Querying Cost and Usage Reports using Amazon Athena — AWS Data Exports](https://docs.aws.amazon.com/cur/latest/userguide/cur-query-athena.html)
**AWS 공식 / 읽기 30분**
CUR 2.0(SQL 테이블명 `COST_AND_USAGE_REPORT`)을 S3 → Athena로 질의. daily report로는 불가능한 **tag × service × region × RI/SP allocation** multi-dimension 분석. LV-003 직결. ([CUR 2.0 컬럼 사전](https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2.html))

### 3. [Detecting unusual spend with AWS Cost Anomaly Detection — AWS Docs](https://docs.aws.amazon.com/cost-management/latest/userguide/manage-ad.html)
**AWS 공식 / 읽기 20분**
`GetAnomalies`가 반환하는 RootCauses·Impact(TotalImpact / TotalActualSpend / TotalExpectedSpend)를 받아 dimension breakdown으로 내려가는 방법론. LV-001 / LV-008 의 시작점.

---

## 🟡 권장 (자기 도구 적용 시 참고)

### 실시간 단가 — Pricing / Spot (LV-002 · LV-004 · LV-005)

| 자료 | 한 줄 설명 |
|------|-----------|
| [AWS Price List API Update — New Query and Metadata Functions (AWS Blog)](https://aws.amazon.com/blogs/aws/aws-price-list-api-update-new-query-and-metadata-functions/) | `GetServices` → `GetAttributeValues` → `GetProducts` 워크플로로 on-demand 단가 동적 조회 |
| [describe_spot_price_history — boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_spot_price_history.html) | family/region/AZ별 spot 단가 시계열. 30일 평균 + interruption 추정의 입력 |
| [Pricing client — boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/pricing.html) | Price List API의 Python 클라이언트 (filter expression 사용법) |

### RI / 추천 자동화 (LV-004 · LV-006 · LV-007)

| 자료 | 한 줄 설명 |
|------|-----------|
| [CostExplorer client (RI Utilization/Coverage) — boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce.html) | `get_reservation_utilization` / `get_reservation_coverage`로 RI 미활용 실시간 추적 |
| [What is AWS Compute Optimizer? — Docs](https://docs.aws.amazon.com/compute-optimizer/latest/ug/what-is-compute-optimizer.html) | EC2/ASG/EBS/Lambda/ECS-Fargate rightsizing 권장. last 14일 metric 기반이라 매주 결과가 달라짐 |
| [get-ec2-instance-recommendations — CLI/API](https://docs.aws.amazon.com/cli/latest/reference/compute-optimizer/get-ec2-instance-recommendations.html) | Compute Optimizer 권장을 Terraform PR로 자동화하는 입력 (LV-007) |
| [Resource requirements — Compute Optimizer](https://docs.aws.amazon.com/compute-optimizer/latest/ug/requirements.html) | Lambda는 메모리 ≤1792MB, EBS는 30시간 연속 attach 등 권장 생성 조건 |

---

## 🟩 한국어 사례 (실전)

### 1. [Amazon Athena를 사용하여 비용 및 사용 보고서 쿼리 — AWS Docs (KR)](https://docs.aws.amazon.com/ko_kr/cur/latest/userguide/cur-query-athena.html)
**AWS 공식 / 읽기 25분**
CUR → S3 → Athena 설정을 한국어로. LV-003 구현 시 가장 먼저 볼 문서.

### 2. [비용 최적화 시리즈 1부: AWS 사용량 시각화로 인사이트 얻기 — AWS 한국 블로그](https://aws.amazon.com/ko/blogs/korea/visualize-and-gain-insights-into-your-aws-cost-and-usage-with-amazon-managed-grafana/)
**AWS 한국 블로그 / 읽기 30분**
CUR + Athena + Managed Grafana 파이프라인. 본인 도구의 출력 레이어 설계 참고.

### 3. [Building an AI-Powered AWS Cost Explorer Using Amazon Bedrock and Athena — Medium](https://jyotinotani.medium.com/building-an-ai-powered-aws-cost-explorer-using-amazon-bedrock-and-athena-ba9d1be891b2)
**2026 / 읽기 25분**
boto3 + Athena + LLM을 묶어 자연어 비용 질의를 만드는 실전 예시. 멀티 에이전트 + live API 결합 아이디어.

---

## 🟢 심화 (시간 남으면)

### 1. [Create your own granular cost dimension using Cost Categories and Amazon Athena — AWS Blog](https://aws.amazon.com/blogs/aws-cloud-financial-management/create-your-own-granular-cost-dimension-using-aws-cost-categories-and-amazon-athena/)
**AWS Cloud Financial Management / 읽기 30분**
Cost Categories로 unit economics(cost/order 등) 차원을 직접 만들어 Athena로 집계.

### 2. [Migration to CUR 2.0 — Cloud Intelligence Dashboards](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/migration-to-cur.html)
**AWS 공식 / 읽기 20분**
기존 CUR(legacy) → CUR 2.0 차이와 쿼리 변경점. fixed column schema의 장점.

### 3. [Cost Optimization Pillar — AWS Well-Architected](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)
**AWS 공식 / 레퍼런스**
live 분석으로 찾은 낭비를 어느 lifecycle 단계에 매핑할지 프레임.

---

## 📋 토론 토픽 (월요일 22:00 세션용)

읽어 오고 본인 도구·시나리오에 대입해서 답 준비:

1. **정적 → live 경계** — 본인 시나리오는 "왜 정적 파일로는 못 푸나"? 어떤 데이터가 raw event(hourly/실시간)여야만 보이나?
2. **mock 모드 설계** — live API와 mock JSON을 같은 분석 파이프라인에 태우려면 인터페이스를 어떻게 추상화? (`detect() → drilldown() → correlate() → report()`)
3. **API rate limit 대응** — `GetCostAndUsage`는 일 호출 제한이 있음. 캐싱·배치·페이지네이션을 어떻게 설계?
4. **단가 신선도** — spot/on-demand 단가를 매 분석마다 live로 갱신할지, 주기적으로 스냅샷할지 trade-off?
5. **페어 비교** — 같은 시나리오를 받은 페어와 설계는 토론, 구현은 독립. 접근 차이(에이전트 구조·단가 처리·출력)를 어떻게 비교?

---

## 🎯 산출물 (다음 주까지)

- [ ] **AWS API 연동 모듈** — 배정 Live API를 호출하는 tool/function (`solution.py` 또는 `solution.ts`)
- [ ] **mock 모드** — 제공된 `mock_responses/*.json`으로 동일 파이프라인 실행 (AWS 계정 없이 데모 가능)
- [ ] **분석 로직** — API 응답 파싱 → 이상 탐지 / 권장 생성 → 구조화된 JSON·Markdown 출력
- [ ] **Report** — `report.md` (설계 결정 / 구현 과정 / 페어 비교 / 회고)
- [ ] **Estimated Monthly Savings** — mock 시나리오 기준 절감 추정액

---

## 📎 참고

- 시나리오 카탈로그 Week 4 (요약): [docs/SCENARIOS_S2.md](SCENARIOS_S2.md)
- 시나리오 카탈로그 Week 4 (상세본): [docs/SCENARIOS_S2_DETAILED.md](SCENARIOS_S2_DETAILED.md)
- 본주 본인 시나리오: Problems → 시즌 2 → Week 4
