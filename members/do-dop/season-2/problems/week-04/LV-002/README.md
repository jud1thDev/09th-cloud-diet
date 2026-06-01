# LV-002: Region/AZ Spot 가격 차이 활용 — 최적 배치 결정 자동화

## Scenario

멀티 리전 환경에서 Spot 인스턴스를 활용하여 비용을 최적화하려 합니다.
리전/AZ별 Spot 가격 차이와 중단율을 분석하여 최적의 배치 전략을 자동으로 결정하는 에이전트를 구축하세요.

## Live APIs

| API | Purpose |
|-----|---------|
| `pricing:GetProducts` | On-Demand 가격 조회 (비교 기준) |
| `ec2:DescribeSpotPriceHistory` | 리전/AZ별 Spot 가격 이력 조회 |

## Task

다음 기능을 수행하는 에이전트를 구축하세요:

1. **가격 비교**: 여러 리전/AZ의 Spot 가격을 On-Demand 대비 할인율로 비교
2. **중단율 분석**: Spot 가격 변동 패턴에서 중단 위험을 추정
3. **최적 배치 추천**: 비용 절감과 안정성을 균형 있게 고려한 배치 전략 제안
4. **Fleet 다각화**: 인스턴스 패밀리/사이즈 다각화 전략 포함

## Deliverables

- `solution.py` 또는 `solution.ts` — 에이전트 코드
- `report.md` — 분석 결과 보고서 (mock 데이터 기반)

## Evaluation Criteria

- 다중 리전/AZ 가격 비교 로직의 정확성
- 중단율 추정 알고리즘의 합리성
- 추천 결과의 실용성 (비용 vs 안정성 트레이드오프)
- 코드 구조 및 에러 핸들링
