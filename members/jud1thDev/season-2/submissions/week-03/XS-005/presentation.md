# XS-005 발표 메모

## 핵심 결론

- 발견 패턴: L3-025, L3-029
- 총 절감 추정: **월 $426.24**

## 발견 이슈

- `L3-025` Single-AZ NAT로 인한 cross-AZ 비용: 4개 리소스
- `L3-029` S3 트래픽 NAT 경유: 6개 리소스

## Emergent finding

- S3 대량 트래픽이 중앙 NAT 경로에서 이중 과금된다
  - `S3-heavy analytics traffic → centralized NAT → NAT processing + cross-AZ transfer`
  - 먼저 S3 Gateway Endpoint로 대량 payload를 제거한 뒤, 남은 egress만 AZ-local NAT로 정리한다.

## 발표 포인트

- 단일 에이전트는 이슈를 나열한다.
- 멀티 에이전트는 서비스 경계를 넘어 비용 흐름을 설명한다.
- 좋은 자동화는 정답을 많이 말하는 것보다, 다음 조치를 더 정확히 정렬한다.
