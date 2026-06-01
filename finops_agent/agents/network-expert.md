---
name: network-expert
domain: network
patterns: [L3-025, LV-006-TA-ELB]
detector_fns: [detect_l3_025, detect_lv006]
---

# Network FinOps Expert

> NAT · ALB · Cross-AZ 트래픽 영역의 낭비를 찾는다.

## 역할

TBD — W2 4단계.

## 입력 신호

- Terraform 리소스 블록: `aws_nat_gateway`, `aws_lb`, `aws_route_table`, `aws_subnet`
- metric: `cross_az_bytes_mb_per_hr`, `nat_bytes_mb_per_hr`, `idle_lb_days`
- Live(W4): Trusted Advisor `idle_load_balancers`

## 출력 포맷

`Finding` dataclass — `pattern_id` · `resource` · `evidence[]` · `recommendation` · `estimated_savings`

## 도메인 원칙

TBD — W2 4단계.
