# LV-006 발표 메모

## 핵심 결론

- 발견 패턴: LV-006-CO-EC2, LV-006-CO-LAMBDA, LV-006-TA-EBS, LV-006-TA-EC2, LV-006-TA-ELB, LV-006-TA-RDS
- 총 절감 추정: **월 $1370.66**

## 발견 이슈

- `LV-006-TA-ELB` Trusted Advisor: idle Load Balancer: 1개 리소스
- `LV-006-TA-EBS` Trusted Advisor: 미연결 EBS 볼륨: 2개 리소스
- `LV-006-TA-RDS` Trusted Advisor: idle RDS: 1개 리소스
- `LV-006-TA-EC2` Trusted Advisor: 저활용 EC2: 1개 리소스
- `LV-006-CO-EC2` Compute Optimizer: EC2 rightsizing: 3개 리소스
- `LV-006-CO-LAMBDA` Compute Optimizer: Lambda 메모리 rightsizing: 3개 리소스

## Emergent finding

- TA와 Compute Optimizer가 동일 EC2를 가리킨다 (cross-source agreement)
  - `TA Cost Optimizing check → CO 14d metric analysis → 동일 인스턴스 ID 매칭 → 단일 권장`
  - 중복 절감액을 더하지 말고 CO 권장 타입 + 절감 추정치 한 줄로 PR을 만든다. TA finding은 PR description의 보강 근거로만 인용한다.

## 발표 포인트

- 단일 에이전트는 이슈를 나열한다.
- 멀티 에이전트는 서비스 경계를 넘어 비용 흐름을 설명한다.
- 좋은 자동화는 정답을 많이 말하는 것보다, 다음 조치를 더 정확히 정렬한다.
