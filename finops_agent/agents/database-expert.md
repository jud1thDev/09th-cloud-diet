---
name: database-expert
domain: database
patterns: [L1-004, L1-010, L2-020, LV-006-TA-RDS]
detector_fns: [detect_l1_004, detect_l1_010, detect_l2_020, detect_lv006]
---

# Database FinOps Expert

> RDS · DynamoDB 영역의 낭비를 찾는다.

## 역할

TBD — W2 4단계.

## 입력 신호

- Terraform 리소스 블록: `aws_db_instance`, `aws_rds_cluster`, `aws_dynamodb_table`
- metric: `connections_avg`, `read_iops_avg`, `consumed_rcu_avg`, `consumed_wcu_avg`
- Live(W4): Trusted Advisor `rds_idle_dbinstance`

## 출력 포맷

`Finding` dataclass — `pattern_id` · `resource` · `evidence[]` · `recommendation` · `estimated_savings`

## 도메인 원칙

TBD — W2 4단계.
