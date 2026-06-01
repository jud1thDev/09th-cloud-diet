terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-2"
}

# ---------------------------------------------------------------------------
# 1. AWS Cost Anomaly Detection
#    Automatically detects cost spikes like the 2026-05-27 EC2/S3 event
# ---------------------------------------------------------------------------

resource "aws_ce_anomaly_monitor" "service_monitor" {
  name              = "lv001-service-anomaly-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
}

resource "aws_sns_topic" "cost_anomaly_alerts" {
  name = "lv001-cost-anomaly-alerts"
}

resource "aws_ce_anomaly_subscription" "daily_alert" {
  name      = "lv001-anomaly-subscription"
  frequency = "DAILY"

  monitor_arn_list = [
    aws_ce_anomaly_monitor.service_monitor.arn,
  ]

  subscriber {
    type    = "SNS"
    address = aws_sns_topic.cost_anomaly_alerts.arn
  }

  # Alert when anomaly impact exceeds $50 (well above normal hourly variance)
  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      values        = ["50"]
      match_options = ["GREATER_THAN_OR_EQUAL"]
    }
  }
}

resource "aws_sns_topic_policy" "cost_anomaly_alerts" {
  arn = aws_sns_topic.cost_anomaly_alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "costalerts.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.cost_anomaly_alerts.arn
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# 2. AWS Budgets — hourly cost guard
#    Alerts when spend exceeds $15/hr (baseline $12.41 + buffer)
# ---------------------------------------------------------------------------

resource "aws_budgets_budget" "hourly_cost_guard" {
  name         = "lv001-hourly-cost-guard"
  budget_type  = "COST"
  limit_amount = "15.00"
  limit_unit   = "USD"
  time_unit    = "HOURLY"

  cost_filter {
    name   = "Region"
    values = ["ap-northeast-2"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_sns_topic_arns  = [aws_sns_topic.cost_anomaly_alerts.arn]
  }
}

# ---------------------------------------------------------------------------
# 3. CloudTrail — required to confirm triggering events for future spikes
#    Covers: EC2, Auto Scaling, ECS, CloudFormation, S3
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "cloudtrail_logs" {
  bucket        = "lv001-cloudtrail-logs-${data.aws_caller_identity.current.account_id}"
  force_destroy = false
}

resource "aws_s3_bucket_policy" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "cloudtrail.amazonaws.com" }
        Action    = "s3:GetBucketAcl"
        Resource  = aws_s3_bucket.cloudtrail_logs.arn
      },
      {
        Effect    = "Allow"
        Principal = { Service = "cloudtrail.amazonaws.com" }
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.cloudtrail_logs.arn}/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
        Condition = {
          StringEquals = { "s3:x-amz-acl" = "bucket-owner-full-control" }
        }
      }
    ]
  })
}

resource "aws_cloudtrail" "cost_spike_trail" {
  name                          = "lv001-cost-spike-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail_logs.id
  include_global_service_events = false
  is_multi_region_trail         = false
  enable_logging                = true

  event_selector {
    read_write_type           = "WriteOnly"
    include_management_events = true
  }

  tags = {
    Purpose = "CostSpikeRootCause"
    Scenario = "LV-001"
  }
}

# ---------------------------------------------------------------------------
# 4. CloudWatch Alarms — EC2 instance count guard (Auto Scaling runaway)
#    Replace <YOUR_ASG_NAME> with the actual Auto Scaling Group name
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "asg_instance_count_guard" {
  alarm_name          = "lv001-asg-instance-count-spike"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "GroupInServiceInstances"
  namespace           = "AWS/AutoScaling"
  period              = 300
  statistic           = "Maximum"
  threshold           = 5  # adjust to expected baseline instance count

  dimensions = {
    AutoScalingGroupName = "<YOUR_ASG_NAME>"
  }

  alarm_actions = [aws_sns_topic.cost_anomaly_alerts.arn]
  alarm_description = "Triggers when EC2 instance count exceeds expected baseline — potential runaway scale-out"
}

# ---------------------------------------------------------------------------
# 5. Savings Plans recommendation (comment — apply via AWS Console/CLI)
#    c5.4xlarge in ap-northeast-2: Compute Savings Plan saves up to 66%
#    vs On-Demand ($0.68/hr On-Demand → ~$0.23/hr with 3-year SP)
#    Purchase via: aws savingsplans purchase-savings-plan ...
# ---------------------------------------------------------------------------

data "aws_caller_identity" "current" {}