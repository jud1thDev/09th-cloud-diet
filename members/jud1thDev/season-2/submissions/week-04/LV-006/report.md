# LV-006 분석 리포트

## 핵심 결과

- 발견 패턴: LV-006-CO-EC2, LV-006-CO-LAMBDA, LV-006-TA-EBS, LV-006-TA-EC2, LV-006-TA-ELB, LV-006-TA-RDS
- 추정 월 절감액: **$1370.66** (Compute Optimizer + Trusted Advisor 권장 합산 (TA × CO 중복 제거))
- 분석 레벨: `L3`

## 발견 이슈

- `LV-006-TA-ELB` Trusted Advisor: idle Load Balancer: 1개 리소스
- `LV-006-TA-EBS` Trusted Advisor: 미연결 EBS 볼륨: 2개 리소스
- `LV-006-TA-RDS` Trusted Advisor: idle RDS: 1개 리소스
- `LV-006-TA-EC2` Trusted Advisor: 저활용 EC2: 1개 리소스
- `LV-006-CO-EC2` Compute Optimizer: EC2 rightsizing: 3개 리소스
- `LV-006-CO-LAMBDA` Compute Optimizer: Lambda 메모리 rightsizing: 3개 리소스

## 핵심 근거

1. LV-006-CO-EC2 root cause
- Compute Optimizer는 최근 14일 CloudWatch 메트릭을 기반으로 OVER_PROVISIONED 인스턴스를 식별한다.
- 대상 인스턴스 3개의 CPU MAX가 모두 권장 사이즈에서도 80% 미만으로 유지될 것으로 예측된다.
- 결정 로직: rank=1 옵션 중 `performanceRisk<3.0`인 것을 채택하고, rank=1이 위험하면 rank=2로 폴백한다.

2. LV-006-CO-LAMBDA root cause
- Compute Optimizer Lambda recommender는 호출별 메모리 활용률을 14일 관찰한다.
- 대상 함수 3개는 모두 Memory MAX가 현재 할당의 50% 미만이라 OVER_PROVISIONED로 분류된다.
- rank=1 권장 메모리만 채택. Duration 변화는 power-tuning이 필요한 별개 의사결정이라 본 권장에서는 다루지 않는다.

3. LV-006-TA-EBS root cause
- Trusted Advisor `Cost Optimizing` 카테고리가 미연결 EBS로 플래그한 리소스 2개.
- 판단 근거(metadata): ap-northeast-2 / vol-0abc123def456789a / gp3 / 500 GiB
- TA는 청구서 단가 기반의 보수적 추정이라 실제 절감 폭은 CO 권장 또는 자체 단가표로 한 번 더 검증해야 한다.

4. LV-006-TA-EC2 root cause
- Trusted Advisor `Cost Optimizing` 카테고리가 저활용 EC2로 플래그한 리소스 1개.
- 판단 근거(metadata): ap-northeast-2 / i-0123456789abcdef0 / m5.2xlarge / CPU avg 2.1% over 14 days
- TA는 청구서 단가 기반의 보수적 추정이라 실제 절감 폭은 CO 권장 또는 자체 단가표로 한 번 더 검증해야 한다.

5. LV-006-TA-ELB root cause
- Trusted Advisor `Cost Optimizing` 카테고리가 idle ELB로 플래그한 리소스 1개.
- 판단 근거(metadata): ap-northeast-2 / my-idle-loadbalancer / Classic Load Balancer / No active back-end instances
- TA는 청구서 단가 기반의 보수적 추정이라 실제 절감 폭은 CO 권장 또는 자체 단가표로 한 번 더 검증해야 한다.

6. LV-006-TA-RDS root cause
- Trusted Advisor `Cost Optimizing` 카테고리가 idle RDS로 플래그한 리소스 1개.
- 판단 근거(metadata): ap-northeast-2 / dev-legacy-database / db.r5.large / 0 connections over 14 days
- TA는 청구서 단가 기반의 보수적 추정이라 실제 절감 폭은 CO 권장 또는 자체 단가표로 한 번 더 검증해야 한다.

## 권장 조치

1. LV-006-CO-EC2: Compute Optimizer가 권장한 인스턴스 타입(performanceRisk<3.0)으로 Terraform PR을 생성한다.

2. LV-006-CO-LAMBDA: Compute Optimizer가 권장한 memory_size로 aws_lambda_function 리소스를 PR로 갱신한다.

3. LV-006-TA-EBS: 30일 이상 미연결된 EBS 볼륨은 스냅샷 후 삭제한다.

4. LV-006-TA-EC2: CPU 평균 5% 미만 인스턴스를 Compute Optimizer 권장 타입으로 다운사이즈한다.

5. LV-006-TA-ELB: 트래픽이 없는 Load Balancer를 제거하거나 backend를 재연결한다.

6. LV-006-TA-RDS: 연결이 없는 RDS는 스냅샷 후 정지/삭제한다.

## 메트릭 관측

- EC2 `prod-api-server-1` — CPU MAX 12.5%, MEMORY MAX 28.3%
- EC2 `prod-worker-3` — CPU MAX 18.7%, MEMORY MAX 45.2%
- EC2 `staging-web-1` — CPU MAX 5.2%, MEMORY MAX 12.8%
- Lambda `data-processor` — Memory MAX 185.0MB, Duration AVG 2340.0ms
- Lambda `image-resizer` — Memory MAX 512.0MB, Duration AVG 890.0ms
- Lambda `notification-sender` — Memory MAX 78.0MB, Duration AVG 450.0ms
- Trusted Advisor flaggedResources 5건

## 단일 vs 멀티 에이전트

| 구분 | 선언 패턴 커버리지 | 리소스 이슈 수 | 컨텍스트 토큰(추정) | LLM 토큰 | wall-clock |
| --- | ---: | ---: | ---: | ---: |
| Single | - | - | 0 | 0 | -s |
| Multi | 1.0 | 11 | 678 | 0 | 0.000853s |

> 탐지는 같은 결정론적 detector registry를 사용하므로 단일/멀티의 **진짜 recall 비교는 이 실행만으로 측정할 수 없다**. 위 수치는 README에 공개된 선언 패턴 대비 커버리지이며, 실제 비교 포인트는 컨텍스트 분할과 토큰 분배다.
>
> 측정 모드: `deterministic_local`. 로컬 모드의 토큰은 추정치이고 wall-clock은 주로 detector 실행 시간이라 LLM 실측 지연이 아니다.

## Cross-service finding

- **TA와 Compute Optimizer가 동일 EC2를 가리킨다 (cross-source agreement)** — TA Cost Optimizing check → CO 14d metric analysis → 동일 인스턴스 ID 매칭 → 단일 권장

## 회고

이 도구는 문제 폴더 내부 입력만 사용해 정적 증거를 모으고, 도메인별 분석 뒤 cross-service 상관관계를 합성한다. 이번 실행에서 멀티 에이전트의 가치는 단순한 패턴 수보다 결합 원인 설명과 조치 순서를 더 선명하게 만드는 데 있었다.
