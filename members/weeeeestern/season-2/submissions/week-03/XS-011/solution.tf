terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

variable "finops_owner" {
  description = "Validated owner used for FinOps allocation tagging."
  type        = string
  nullable    = false

  validation {
    condition     = length(trimspace(var.finops_owner)) > 0
    error_message = "finops_owner must be a non-empty validated owner."
  }
}

variable "finops_service" {
  description = "Validated service name used for FinOps allocation tagging."
  type        = string
  nullable    = false

  validation {
    condition     = length(trimspace(var.finops_service)) > 0
    error_message = "finops_service must be a non-empty validated service name."
  }
}

variable "finops_cost_center" {
  description = "Validated cost center used for FinOps allocation tagging."
  type        = string
  nullable    = false

  validation {
    condition     = length(trimspace(var.finops_cost_center)) > 0
    error_message = "finops_cost_center must be a non-empty validated cost center."
  }
}

variable "comp1_environment" {
  description = "Validated environment for Component 1 RDS resources, which were missing Environment tags in source Terraform."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["dev", "test", "qa", "staging", "production"], lower(var.comp1_environment))
    error_message = "comp1_environment must be one of: dev, test, qa, staging, production."
  }
}

# =================================================================
# Component 1/2 - seeded from L2-020
# =================================================================

# Note: resource names with hyphens may need normalization in production Terraform.
# Suspected read replica misuse is not automatically applied. Validate application endpoint routing, VPC Flow Logs, replica metrics, and cost/transfer evidence before removal or downsizing.
resource "aws_db_instance" "comp1_db-instance-ebfxrm" {
  identifier     = "db-instance-ebfxrm"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.r5.xlarge"

  allocated_storage = 500
  storage_type      = "gp3"

  multi_az = false

  replicate_source_db = aws_db_instance.comp1_db-instance-ucurem.identifier

  backup_retention_period = 7

  skip_final_snapshot = false

  tags = {
    Name        = "db-instance-ebfxrm"
    Role        = "read_replica"
    Environment = var.comp1_environment
    Owner       = var.finops_owner
    Service     = var.finops_service
    CostCenter  = var.finops_cost_center
  }
}

# Note: resource names with hyphens may need normalization in production Terraform.
# Suspected read replica misuse is not automatically applied. Validate application endpoint routing, VPC Flow Logs, replica metrics, and cost/transfer evidence before removal or downsizing.
resource "aws_db_instance" "comp1_db-instance-7xmaoj" {
  identifier     = "db-instance-7xmaoj"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.r5.xlarge"

  allocated_storage = 500
  storage_type      = "gp3"

  multi_az = false

  replicate_source_db = aws_db_instance.comp1_db-instance-ucurem.identifier

  backup_retention_period = 7

  skip_final_snapshot = false

  tags = {
    Name        = "db-instance-7xmaoj"
    Role        = "read_replica"
    Environment = var.comp1_environment
    Owner       = var.finops_owner
    Service     = var.finops_service
    CostCenter  = var.finops_cost_center
  }
}

# Note: resource names with hyphens may need normalization in production Terraform.
# Suspected read replica misuse is not automatically applied. Validate application endpoint routing, VPC Flow Logs, replica metrics, and cost/transfer evidence before removal or downsizing.
resource "aws_db_instance" "comp1_db-instance-auqu1s" {
  identifier     = "db-instance-auqu1s"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.r5.xlarge"

  allocated_storage = 500
  storage_type      = "gp3"

  multi_az = false

  replicate_source_db = aws_db_instance.comp1_db-instance-ucurem.identifier

  backup_retention_period = 7

  skip_final_snapshot = false

  tags = {
    Name        = "db-instance-auqu1s"
    Role        = "read_replica"
    Environment = var.comp1_environment
    Owner       = var.finops_owner
    Service     = var.finops_service
    CostCenter  = var.finops_cost_center
  }
}

# Note: resource names with hyphens may need normalization in production Terraform.
resource "aws_db_instance" "comp1_db-instance-ucurem" {
  identifier     = "db-instance-ucurem"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.r5.xlarge"

  allocated_storage = 500
  storage_type      = "gp3"

  multi_az = true

  backup_retention_period = 7

  skip_final_snapshot = false

  tags = {
    Name        = "db-instance-ucurem"
    Role        = "primary"
    Environment = var.comp1_environment
    Owner       = var.finops_owner
    Service     = var.finops_service
    CostCenter  = var.finops_cost_center
  }
}

# =================================================================
# Component 2/2 - seeded from L1-004
# =================================================================

# Note: resource names with hyphens may need normalization in production Terraform.
# Dev Multi-AZ disabled by static Environment=dev rule; validate availability requirements before any further capacity or lifecycle changes.
resource "aws_db_instance" "comp2_db-instance-luhltf" {
  identifier     = "db-instance-luhltf"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.r5.large"

  allocated_storage = 100
  storage_type      = "gp3"

  multi_az = false

  backup_retention_period = 7

  skip_final_snapshot = false

  tags = {
    Name        = "db-instance-luhltf"
    Environment = "dev"
    Owner       = var.finops_owner
    Service     = var.finops_service
    CostCenter  = var.finops_cost_center
  }
}

# Note: resource names with hyphens may need normalization in production Terraform.
# Dev Multi-AZ disabled by static Environment=dev rule; validate availability requirements before any further capacity or lifecycle changes.
resource "aws_db_instance" "comp2_db-instance-tj6z5f" {
  identifier     = "db-instance-tj6z5f"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.r5.large"

  allocated_storage = 100
  storage_type      = "gp3"

  multi_az = false

  backup_retention_period = 7

  skip_final_snapshot = false

  tags = {
    Name        = "db-instance-tj6z5f"
    Environment = "dev"
    Owner       = var.finops_owner
    Service     = var.finops_service
    CostCenter  = var.finops_cost_center
  }
}

# Note: resource names with hyphens may need normalization in production Terraform.
resource "aws_db_instance" "comp2_db-instance-ic9a67" {
  identifier     = "db-instance-ic9a67"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.r5.large"

  allocated_storage = 100
  storage_type      = "gp3"

  multi_az = true

  backup_retention_period = 7

  skip_final_snapshot = false

  tags = {
    Name        = "db-instance-ic9a67"
    Environment = "production"
    Owner       = var.finops_owner
    Service     = var.finops_service
    CostCenter  = var.finops_cost_center
  }
}