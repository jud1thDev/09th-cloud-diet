# XS-005 분석 리포트

## 핵심 결과

- 발견 패턴: L3-025, L3-029
- 추정 월 절감액: **$426.24** (`cost_report.summary.avg_monthly_waste` 기준 총액)
- 분석 레벨: `L3`

## 발견 이슈

- `L3-025` Single-AZ NAT로 인한 cross-AZ 비용: 4개 리소스
- `L3-029` S3 트래픽 NAT 경유: 6개 리소스

## 핵심 근거

1. L3-025 root cause
- `comp2_nat-gateway-r4cxxz`의 `cross_az_bytes_mb_per_hr` 평균이 `100.0` MB/hr로 계속 0보다 크다.
- 문제 route table은 `associated_subnets = "all_private"`라 여러 AZ subnet을 한 경로에 몰아넣는다.
- 반대로 입력 안의 AZ-local NAT 후보 3개는 cross-AZ 평균이 `0.0`이라, 현재 낭비가 트래픽 양 자체가 아니라 경로 선택에서 생긴다는 점을 뒷받침한다.

2. L3-029 root cause
- 문제 리소스에서는 `nat_bytes_out_mb_per_hr`와 `s3_request_count_per_hr`가 함께 보이고, 대표 평균은 각각 `100.0` MB/hr와 `100.0` req/hr다.
- S3 접근을 private 경로로 흡수해야 할 endpoint 구성이 fleet 전체에 적용되지 않았다. Terraform provider는 `us-east-1`인데 기존 S3 endpoint service_name은 `ap-northeast-2`를 가리켜 현재 리전 경로를 보호하지 못한다.
- 그 결과 청구서는 NAT bytes로만 보이지만, 실제 payload는 S3 접근과 강하게 결합되어 있다.

## 권장 조치

1. L3-025 조치
- `all_private`로 뭉친 문제 route table을 AZ-local 경로(`same_az_private`)로 전환한다.
- 이미 존재하는 AZ별 NAT 경로를 사용해 각 subnet이 같은 AZ의 NAT를 타도록 정리한다.
- 전환 후 `cross_az_bytes_mb_per_hr`가 0으로 내려가는지 확인한 뒤 중앙 경로 의존을 제거한다.

2. L3-029 조치
- 기존 S3 Gateway Endpoint를 현재 provider 리전에 맞는 service name으로 수정한다.
- 각 private route table마다 S3 endpoint association 리소스를 직접 참조로 추가한다.
- 적용 후 NAT bytes와 S3 direct bytes를 함께 확인해 우회 경로가 사라졌는지 검증한다.

## 단일 vs 멀티 에이전트

| 구분 | 선언 패턴 커버리지 | 리소스 이슈 수 | 컨텍스트 토큰(추정) | LLM 토큰 | wall-clock |
| --- | ---: | ---: | ---: | ---: |
| Single | 1.0 | 10 | 6561 | 315 | 0.000299s |
| Multi | 1.0 | 10 | 6369 | 443 | 0.000173s |

> 탐지는 같은 결정론적 detector registry를 사용하므로 단일/멀티의 **진짜 recall 비교는 이 실행만으로 측정할 수 없다**. 위 수치는 README에 공개된 선언 패턴 대비 커버리지이며, 실제 비교 포인트는 컨텍스트 분할과 토큰 분배다.
>
> 측정 모드: `deterministic_local`. 로컬 모드의 토큰은 추정치이고 wall-clock은 주로 detector 실행 시간이라 LLM 실측 지연이 아니다.

## Cross-service finding

- **S3 대량 트래픽이 중앙 NAT 경로에서 이중 과금된다** — S3-heavy analytics traffic → centralized NAT → NAT processing + cross-AZ transfer

## 회고

이 도구는 문제 폴더 내부 입력만 사용해 정적 증거를 모으고, 도메인별 분석 뒤 cross-service 상관관계를 합성한다. 이번 실행에서 멀티 에이전트의 가치는 단순한 패턴 수보다 결합 원인 설명과 조치 순서를 더 선명하게 만드는 데 있었다.
