# LV-006: Trusted Advisor + Compute Optimizer → 자동 PR 생성

## Scenario

AWS Trusted Advisor와 Compute Optimizer의 권장사항을 수동으로 확인하고 적용하는 것은 비효율적입니다.
두 서비스의 결과를 자동으로 수집하여 Terraform PR을 생성하는 에이전트를 구축하세요.

## Live APIs

| API | Purpose |
|-----|---------|
| `support:DescribeTrustedAdvisorCheckResult` | Trusted Advisor 비용 최적화 결과 조회 |
| `compute-optimizer:GetEC2InstanceRecommendations` | EC2 rightsizing 추천 조회 |

## Task

다음 기능을 수행하는 에이전트를 구축하세요:

1. **TA 결과 수집**: Trusted Advisor의 비용 최적화 카테고리 결과 수집 (idle ELB, unattached EBS 등)
2. **CO 추천 수집**: Compute Optimizer의 EC2/Lambda rightsizing 추천 수집
3. **Terraform 변경 생성**: 추천 내용을 반영한 Terraform 코드 변경 생성
4. **PR 생성**: 비용 절감 예상액을 포함한 PR body 작성

## Deliverables

- `solution.py` 또는 `solution.ts` — 에이전트 코드
- `report.md` — 분석 결과 보고서 (mock 데이터 기반)

## Evaluation Criteria

- TA/CO 결과를 정확하게 파싱하고 통합하는가
- Terraform 코드 변경이 유효한가
- PR body에 비용 절감 정보가 명확하게 포함되어 있는가
- 코드 구조 및 에러 핸들링
