# LV-008: Cost Anomaly Detection → 자동 root-cause 분석

## Scenario

AWS Cost Anomaly Detection에서 이상 비용이 탐지되었습니다.
탐지된 anomaly를 자동으로 분석하여 multi-dimensional drill-down과 CloudTrail 이벤트 상관 분석을 수행하고,
자동화된 root-cause 보고서를 생성하는 에이전트를 구축하세요.

## Live APIs

| API | Purpose |
|-----|---------|
| `ce:GetAnomalies` | 비용 이상 탐지 결과 조회 |
| `ce:GetCostAndUsage` (multiple GroupBy) | 다차원 비용 분석 |
| CloudTrail event lookup | 이벤트 상관 분석 |

## Task

다음 기능을 수행하는 에이전트를 구축하세요:

1. **Anomaly 처리**: Cost Anomaly Detection 알림을 수신하고 파싱
2. **Multi-dimensional Drill-down**: Service → UsageType → Region → Account 순으로 단계적 분석
3. **CloudTrail 상관 분석**: anomaly 발생 시점 전후의 API 호출 패턴 분석
4. **Root-cause 보고서**: 자동화된 보고서 생성 (원인, 영향, 추천 조치 포함)

## Deliverables

- `solution.py` 또는 `solution.ts` — 에이전트 코드
- `report.md` — 분석 결과 보고서 (mock 데이터 기반)

## Evaluation Criteria

- Anomaly 데이터 파싱 및 우선순위 결정 로직
- Multi-dimensional drill-down의 체계성
- CloudTrail 이벤트와의 상관관계 분석 품질
- Root-cause 보고서의 actionability
- 코드 구조 및 에러 핸들링
