# Week 4 — Live 환경 분석 (정적 분석 한계 사례)

> 데드라인: 2026-06-01 (월요일 22:00 세션 전까지)
> 테마: 실시간 AWS API 연동 에이전트 구현

---

## 이번 주차 목표

Week 2~3에서는 **정적 파일(main.tf + cost_report + metrics)** 기반 분석이었습니다.
Week 4부터는 **실시간 AWS API를 호출해야만 풀 수 있는** 시나리오를 다룹니다.

본인 도구에 AWS SDK(boto3/AWS CLI) 연동 기능을 추가하고,
Live API 응답을 기반으로 분석·권장을 자동 생성하는 것이 과제입니다.

---

## 시나리오 배정

| Member | 시나리오 | 핵심 Live API | 페어 |
|--------|---------|--------------|------|
| dev-jiseok | LV-008 | Cost Anomaly Detection → 자동 root-cause 분석 | 단독 (리더) |
| seoyoungleeme | LV-001 + LV-003 | GetCostAndUsage + CUR 2.0 Athena | ↔ juanxiu |
| juanxiu | LV-001 + LV-003 | GetCostAndUsage + CUR 2.0 Athena | ↔ seoyoungleeme |
| 7910trio | LV-004 + LV-005 | RI Utilization + Spot Interruption | ↔ m1cks |
| m1cks | LV-004 + LV-005 | RI Utilization + Spot Interruption | ↔ 7910trio |
| jud1thDev | LV-006 + LV-007 | Trusted Advisor + Compute Optimizer → PR 자동 생성 | ↔ 600gramSik |
| 600gramSik | LV-006 + LV-007 | Trusted Advisor + Compute Optimizer → PR 자동 생성 | ↔ jud1thDev |
| do-dop | LV-002 | Region/AZ Spot 가격 차이 활용 | 단독 |
| weeeeestern | LV-008 | Cost Anomaly Detection → 자동 root-cause 분석 | 단독 |

---

## 과제 형식

### A. 구현 (필수)

본인 에이전트 도구에 다음 기능을 추가:

1. **AWS API 연동 모듈** — 배정된 Live API를 호출하는 tool/function
2. **분석 로직** — API 응답을 파싱하여 이상 탐지 / 권장 생성
3. **출력 형식** — 분석 결과를 구조화된 JSON 또는 Markdown으로 출력

### B. 데모 (필수)

실제 AWS 계정이 없어도 되도록 **mock 모드** 지원:
- 제공된 mock response JSON으로 동일 분석 파이프라인 실행
- 실제 AWS 계정이 있으면 live 모드로도 실행 가능

### C. 제출물

`Submit Answer` 페이지에서 시나리오 ID (예: `LV-001`)로 다음을 제출:
- **구현 코드** — Live API 연동 모듈 (GitHub repo link 또는 코드 첨부)
- **Mock 데모 결과** — mock data 기반 분석 실행 결과 스크린샷 또는 output
- **Report** — `report.md` (설계 결정, 구현 과정, 페어 비교, 회고)
- **Estimated Monthly Savings** — mock 시나리오 기준 절감 추정액

---

## Mock Data 제공

각 시나리오별 mock response는 `members/{username}/season-2/problems/week-04/{scenario}/mock_responses/` 에 생성됩니다.

---

## 평가 기준

| 항목 | 배점 | 설명 |
|------|------|------|
| API 연동 구현 완성도 | 30 | Live API 호출 + 응답 파싱 + 에러 핸들링 |
| 분석 로직 정확성 | 25 | mock data에서 올바른 이상/권장 도출 |
| 자동화 수준 | 20 | 수동 개입 없이 end-to-end 실행 가능 여부 |
| 코드 품질 + 확장성 | 10 | 다른 API 추가 시 확장 용이한 구조 |
| 페어 비교 + 회고 | 15 | 같은 시나리오를 다른 접근으로 풀어본 비교 분석 |

---

## 힌트

- **boto3 session 관리**: `AWS_PROFILE` 또는 `AWS_ACCESS_KEY_ID` 환경변수로 인증
- **Mock 모드 패턴**: `if mock_mode: response = json.load(mock_file) else: response = client.get_cost_and_usage(...)`
- **페어 작업**: 같은 시나리오를 받은 페어와 주 중에 설계 토론 → 구현은 독립 → 제출 시 비교 분석
- **Cost Explorer API 주의**: `ce:GetCostAndUsage`는 일 14회 호출 제한 있음 → mock 우선 개발
