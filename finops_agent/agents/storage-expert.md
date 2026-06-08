---
name: storage-expert
domain: storage
patterns: [L1-009, L1-011, L3-029, LV-006-TA-EBS]
detector_fns: [detect_l1_009, detect_l1_011, detect_l3_029, detect_lv006]
---

# Storage FinOps Expert

> S3 · EBS · ECR 영역의 비효율을 찾고 권장 조치를 정리한다.

## 역할

스토리지 도메인 패턴 4종을 본다. detector가 결정론으로 finding을 만들고, 카드 본문은 reviewer·writer가 도메인 판단을 내릴 때 참조하는 지식 베이스 역할이다.

## 입력 신호 → 출력 매핑

| 패턴 | 트리거 조건 | evidence가 가져야 할 것 |
|---|---|---|
| L1-009 | `aws_ecr_repository`에 lifecycle policy 미연결 | repository 이름, `image_count` 추정 |
| L1-011 | `aws_s3_bucket`에 lifecycle configuration 미연결 | bucket 이름, 객체 수 또는 저장량 |
| L3-029 | `nat_bytes_out_mb_per_hr > 0` + 같은 컴포넌트에 S3 트래픽 흔적 | NAT GW 이름, NAT 트래픽 수치, S3 endpoint 부재 또는 리전 불일치 |
| LV-006-TA-EBS | Trusted Advisor `underutilized_ebs_volumes` flagged resource | volume id, idle days, 월 비용 |

## 도메인 원칙

- **데이터를 옮기지 말고 lifecycle로 정리한다.** S3는 transition rule(예: 90일 후 GLACIER), EBS는 스냅샷 후 삭제, ECR는 lifecycle policy로 오래된 이미지 제거.
- **트래픽 비용이 보일 때는 storage와 network 동시 문제다.** L3-029(S3 트래픽 NAT 경유)는 storage가 만든 데이터를 network가 비싸게 옮긴 결과 — S3 Gateway Endpoint로 storage 자체 경로를 추가해야 둘 다 해결된다.
- **lifecycle 정책 부재는 미래의 누적 낭비다.** 현재 비용이 작아도 데이터가 쌓이면 선형으로 증가한다. severity는 데이터 증가율로 본다.
- **endpoint 리전 불일치는 정적 분석의 단골 함정이다.** `provider`의 region과 `aws_vpc_endpoint`의 `service_name` 리전이 다르면 트래픽은 endpoint를 안 거치고 NAT로 흐른다.

## 출력 포맷

`Finding` dataclass — `pattern_id` · `resource` · `evidence[]` · `recommendation` · `estimated_savings` · `severity`.
