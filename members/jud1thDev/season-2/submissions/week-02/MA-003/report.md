# MA-003 분석 리포트

## 핵심 결과

- 발견 패턴: L1-009, L3-031, L3-038
- 추정 월 절감액: **$8343.19** (`cost_report.summary.avg_monthly_waste` 기준 총액)
- 분석 레벨: `L3`

## 발견 이슈

- `L3-038` EKS 노드 과잉 프로비저닝: 20개 리소스
- `L1-009` ECR lifecycle 정책 부재: 3개 리소스
- `L3-031` 비용 할당 태그 누락: 51개 리소스

## 핵심 근거

1. L1-009 root cause
- ECR repository와 lifecycle 정책이 1:1로 함께 정의되는 구조가 아니라, 일부 repo에만 정책이 붙었다.
- 정책이 없는 repo는 만료 기준이 없어 이미지가 무한히 누적된다.
- ECR repository는 존재하지만 같은 컴포넌트에 lifecycle 정책 리소스가 없다. 정책 미적용 repo의 image_count 평균 370개로 이미지가 정리 없이 누적되고 있다.

2. L3-031 root cause
- AWS Organizations Tag Policy/SCP로 필수 태그를 강제하지 않았고 provider default_tags도 없어, 태그 적용이 리소스 작성자 재량에 맡겨졌다.
- Terraform plan 단계에 태그 누락을 차단하는 정책 검증 게이트가 없어 비준수 리소스가 그대로 배포됐다.
- provider 블록에 default_tags가 없고, cost-center/team/environment/project 태그가 리소스별로 누락되어 있다. 미준수 리소스의 tag_coverage 평균이 0.0%로 사실상 태깅되지 않았다. unallocated_spend_ratio 평균 49.6%만큼 비용이 미할당 상태로 집계된다.

3. L3-038 root cause
- pod resource request가 실제 사용량을 크게 초과해, 낮은 부하에도 노드가 다수 필요한 것처럼 스케줄링된다.
- 그 결과 노드 인스턴스 타입이 피크 가정에 맞춰 m5.2xlarge로 고정됐다.
- m5.2xlarge 노드가 다수 존재해 노드 플릿이 과도하게 크다. 해당 노드의 node_cpu_percent 평균 15.0%로 프로비저닝 대비 사용률이 매우 낮다.

## 권장 조치

1. L1-009 조치
- lifecycle 정책이 없는 ECR repository에 만료 정책을 추가해 오래된 이미지를 자동 정리한다.
- 신규 repo 누락을 막도록 repository와 lifecycle 정책을 함께 생성하는 구조로 정리한다.

2. L3-031 조치
- provider default_tags로 공통 태그 기준선을 깔고, 리소스별 cost-center/team/environment/project를 채운다.
- AWS Organizations Tag Policy로 필수 태그를 강제하고, CI 파이프라인에 태그 검증 게이트를 추가한다.

3. L3-038 조치
- 과잉 프로비저닝된 m5.2xlarge 노드를 m5.large로 다운그레이드한다.
- pod resource request를 실측 사용량 기준으로 재산정해 노드 수요 자체를 줄인다.

## 메트릭 관측

- EKS 노드 `node_cpu_percent` 평균 15.0% — 프로비저닝 대비 저사용
- 정책 미적용 ECR `image_count` 평균 370개 — 이미지 누적
- 미준수 리소스 `tag_coverage` 평균 0.0% — 비용 귀속 불가

## 단일 vs 멀티 에이전트

| 구분 | 선언 패턴 커버리지 | 리소스 이슈 수 | 컨텍스트 토큰(추정) | LLM 토큰 | wall-clock |
| --- | ---: | ---: | ---: | ---: |
| Single | 1.0 | 74 | 14171 | 2094 | 0.001319s |
| Multi | 1.0 | 74 | 14133 | 914 | 0.000983s |

> 탐지는 같은 결정론적 detector registry를 사용하므로 단일/멀티의 **진짜 recall 비교는 이 실행만으로 측정할 수 없다**. 위 수치는 README에 공개된 선언 패턴 대비 커버리지이며, 실제 비교 포인트는 컨텍스트 분할과 토큰 분배다.
>
> 측정 모드: `deterministic_local`. 로컬 모드의 토큰은 추정치이고 wall-clock은 주로 detector 실행 시간이라 LLM 실측 지연이 아니다.

## Cross-service finding

- 없음

## 회고

이 도구는 문제 폴더 내부 입력만 사용해 정적 증거를 모으고, 도메인별 분석 뒤 cross-service 상관관계를 합성한다. 이번 실행에서 멀티 에이전트의 가치는 단순한 패턴 수보다 결합 원인 설명과 조치 순서를 더 선명하게 만드는 데 있었다.
