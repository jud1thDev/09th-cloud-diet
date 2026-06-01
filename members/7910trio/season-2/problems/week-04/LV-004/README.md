# LV-004: RI 실시간 추적 + Spot Interruption 패턴 학습

## Scenario

Reserved Instances의 활용률이 불균형하고, Spot 인스턴스 중단이 빈번하게 발생하고 있습니다.
RI 활용률을 실시간 추적하고 Spot 중단 패턴을 학습하여 최적화 전략을 제안하는 에이전트를 구축하세요.

## Live APIs

| API | Purpose |
|-----|---------|
| `ce:GetReservationUtilization` | RI 활용률 조회 |
| `ce:GetReservationCoverage` | RI 커버리지 조회 |
| `ec2:DescribeSpotPriceHistory` | Spot 가격 이력 및 중단 패턴 분석 |

## Task

다음 기능을 수행하는 에이전트를 구축하세요:

1. **RI 활용률 분석**: 활용률이 낮은 RI를 식별하고 sell/modify 추천
2. **RI 커버리지 분석**: 커버리지가 낮은 서비스에 추가 RI 구매 제안
3. **Spot 중단 패턴**: 시간대/인스턴스 타입별 중단 패턴 학습
4. **Fleet 다각화 전략**: 중단 위험을 분산하는 인스턴스 mix 제안

## Deliverables

- `solution.py` 또는 `solution.ts` — 에이전트 코드
- `report.md` — 분석 결과 보고서 (mock 데이터 기반)

## Evaluation Criteria

- RI 활용률/커버리지 분석의 정확성
- Spot 중단 패턴 학습 로직의 합리성
- 최적화 추천의 실행 가능성 (sell/modify/diversify)
- 코드 구조 및 에러 핸들링
