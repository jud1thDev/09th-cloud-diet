---
name: compute-expert
domain: compute
patterns: [L2-014, L2-015, L3-038, LV-006-TA-EC2, LV-006-CO-EC2, LV-006-CO-LAMBDA]
detector_fns: [detect_l2_014, detect_l2_015, detect_l3_038, detect_lv006]
---

# Compute FinOps Expert

> Lambda · EC2 · EKS 영역의 낭비를 찾고 권장 조치를 정리한다.

## 역할

TBD — W2 3단계에서 storage-expert 본문 확정 후 같은 형식으로 채운다.

## 입력 신호

- Terraform 리소스 블록: `aws_lambda_function`, `aws_instance`, `aws_eks_node_group`
- metric: `memory_mb_used_avg`, `duration_ms_p99`, `cpu_utilization_avg`, `node_count_actual`
- Live(W4): Trusted Advisor `low_utilization_ec2`, Compute Optimizer `OVER_PROVISIONED` 권장

## 출력 포맷

`Finding` dataclass — `pattern_id` · `resource` · `evidence[]` · `recommendation` · `estimated_savings`

## 도메인 원칙

TBD — W2 3~4단계.
