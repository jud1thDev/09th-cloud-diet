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


# ═══════════════════════════════════════════════════════════════
# Component 1/3 · L3-032 FIX: m5 RI Family Mismatch
# CHANGE: 10× m5.xlarge RI (0% util) → EC2 Marketplace 매각 + Compute SP 전환
# EF-001: Organizations 활성화(comp3) 후 RI sharing 확인 후 매각 권고
# ═══════════════════════════════════════════════════════════════

resource "aws_instance" "comp1_instance-vqmir2" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "c5.xlarge"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-vqmir2" }
}

resource "aws_instance" "comp1_instance-ovuo8z" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "c5.xlarge"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-ovuo8z" }
}

resource "aws_instance" "comp1_instance-0us7i9" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "c5.xlarge"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-0us7i9" }
}

resource "aws_instance" "comp1_instance-6e8w85" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "c5.xlarge"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-6e8w85" }
}

resource "aws_instance" "comp1_instance-m0aqcs" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "c5.xlarge"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-m0aqcs" }
}

resource "aws_instance" "comp1_instance-aai2cd" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "r5.xlarge"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-aai2cd" }
}

resource "aws_instance" "comp1_instance-nbofri" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "r5.xlarge"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-nbofri" }
}

resource "aws_instance" "comp1_instance-d4l8ya" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "r5.xlarge"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-d4l8ya" }
}

resource "aws_instance" "comp1_instance-sa44zv" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "r5.xlarge"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-sa44zv" }
}

resource "aws_instance" "comp1_instance-kkzkn2" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "r5.xlarge"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-kkzkn2" }
}

# ──────────────────────────────────────────────────────────────────────────
# [REMOVED] 10× m5.xlarge RI data sources (0% utilization, wrong family)
# Action: aws ec2 describe-reserved-instances → list on EC2 RI Marketplace
#   IDs: r942li, 9tddqp, uwfsvh, 5r3djc, 7vmg9u, ywm60x, rdziwy, gj8b61, rvk2md, f3uh30
# EF-001: After comp3 Organizations fix → check if any org account runs m5.xlarge
#         If yes: RI sharing covers them; if no: Marketplace매각
# ──────────────────────────────────────────────────────────────────────────

# [NEW] Compute SP: c5.xlarge×5 + r5.xlarge×5 커버 (family-agnostic)
# c5.xlarge SP: $0.136/hr (20% vs $0.170 OD) × 5 = $0.680/hr
# r5.xlarge SP: $0.202/hr (20% vs $0.252 OD) × 5 = $1.010/hr
# Total commitment: $1.69/hr (covers both families under single Compute SP)
resource "aws_ce_savings_plan" "comp1_compute_sp" {
  savings_plan_type      = "Compute"
  payment_option         = "NO_UPFRONT"
  term_duration_in_years = 1
  hourly_commitment      = "1.69"
  tags = { Name = "comp1-c5r5-compute-sp"; Component = "L3-032-fix" }
}

# [UNCHANGED] m5.large×5 + m5.large RI×5 (100% utilization — 정상)
resource "aws_instance" "comp1_instance-251oy4" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.large"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-251oy4" }
}

resource "aws_instance" "comp1_instance-grawqj" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.large"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-grawqj" }
}

resource "aws_instance" "comp1_instance-zsf5ae" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.large"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-zsf5ae" }
}

resource "aws_instance" "comp1_instance-4wybba" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.large"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-4wybba" }
}

resource "aws_instance" "comp1_instance-4gvhlt" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.large"
  subnet_id     = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-4gvhlt" }
}

data "aws_ec2_reserved_instances_offerings" "ec2-reserved-instances-5cpb3j" {
  instance_type = "m5.large"; offering_type = "All Upfront"; product_description = "Linux/UNIX"
  filter { name = "duration"; values = ["31536000"] }
}

data "aws_ec2_reserved_instances_offerings" "ec2-reserved-instances-z9ym40" {
  instance_type = "m5.large"; offering_type = "All Upfront"; product_description = "Linux/UNIX"
  filter { name = "duration"; values = ["31536000"] }
}

data "aws_ec2_reserved_instances_offerings" "ec2-reserved-instances-e8i4oh" {
  instance_type = "m5.large"; offering_type = "All Upfront"; product_description = "Linux/UNIX"
  filter { name = "duration"; values = ["31536000"] }
}

data "aws_ec2_reserved_instances_offerings" "ec2-reserved-instances-m4d66x" {
  instance_type = "m5.large"; offering_type = "All Upfront"; product_description = "Linux/UNIX"
  filter { name = "duration"; values = ["31536000"] }
}

data "aws_ec2_reserved_instances_offerings" "ec2-reserved-instances-otpgpg" {
  instance_type = "m5.large"; offering_type = "All Upfront"; product_description = "Linux/UNIX"
  filter { name = "duration"; values = ["31536000"] }
}


# ═══════════════════════════════════════════════════════════════
# Component 2/3 · L3-033 FIX: Compute SP Coverage 60%→75%
# EF-002: Organizations 활성화(comp3) 후 구매 시 org-level SP로 자동 전환
# ═══════════════════════════════════════════════════════════════

resource "aws_instance" "comp2_instance-3sjdrc" {
  ami = "ami-0abcdef1234567890"; instance_type = "m5.large"; subnet_id = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-3sjdrc" }
}

resource "aws_instance" "comp2_instance-b36tyr" {
  ami = "ami-0abcdef1234567890"; instance_type = "m5.large"; subnet_id = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-b36tyr" }
}

resource "aws_instance" "comp2_instance-g05u5f" {
  ami = "ami-0abcdef1234567890"; instance_type = "m5.large"; subnet_id = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-g05u5f" }
}

resource "aws_instance" "comp2_instance-jn2k4i" {
  ami = "ami-0abcdef1234567890"; instance_type = "m5.large"; subnet_id = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-jn2k4i" }
}

resource "aws_instance" "comp2_instance-8r8hm7" {
  ami = "ami-0abcdef1234567890"; instance_type = "m5.large"; subnet_id = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-8r8hm7" }
}

resource "aws_lambda_function" "comp2_lambda-function-r08abc" {
  function_name = "lambda-function-r08abc"; role = aws_iam_role.lambda-function-r08abc_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-r08abc" }
}

resource "aws_lambda_function" "comp2_lambda-function-0fxkv0" {
  function_name = "lambda-function-0fxkv0"; role = aws_iam_role.lambda-function-0fxkv0_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-0fxkv0" }
}

resource "aws_lambda_function" "comp2_lambda-function-6sqlcx" {
  function_name = "lambda-function-6sqlcx"; role = aws_iam_role.lambda-function-6sqlcx_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-6sqlcx" }
}

resource "aws_lambda_function" "comp2_lambda-function-ydcaiw" {
  function_name = "lambda-function-ydcaiw"; role = aws_iam_role.lambda-function-ydcaiw_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-ydcaiw" }
}

resource "aws_lambda_function" "comp2_lambda-function-nd8r4p" {
  function_name = "lambda-function-nd8r4p"; role = aws_iam_role.lambda-function-nd8r4p_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-nd8r4p" }
}

resource "aws_lambda_function" "comp2_lambda-function-03uqz0" {
  function_name = "lambda-function-03uqz0"; role = aws_iam_role.lambda-function-03uqz0_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-03uqz0" }
}

resource "aws_lambda_function" "comp2_lambda-function-h9yspc" {
  function_name = "lambda-function-h9yspc"; role = aws_iam_role.lambda-function-h9yspc_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-h9yspc" }
}

resource "aws_lambda_function" "comp2_lambda-function-k53vro" {
  function_name = "lambda-function-k53vro"; role = aws_iam_role.lambda-function-k53vro_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-k53vro" }
}

resource "aws_ecs_service" "comp2_ecs-service-wybkif" {
  name = "ecs-service-wybkif"; cluster = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp2_ecs-service-wybkif.arn
  desired_count = 4; launch_type = "FARGATE"; platform_version = "LATEST"
  network_configuration {
    subnets = var.private_subnet_ids
    security_groups = [aws_security_group.ecs-service-wybkif_sg.id]
    assign_public_ip = false
  }
  tags = { Name = "ecs-service-wybkif" }
}

resource "aws_ecs_task_definition" "comp2_ecs-service-wybkif" {
  family = "ecs-service-wybkif"; requires_compatibilities = ["FARGATE"]; network_mode = "awsvpc"
  cpu = "1024"; memory = "2048"
  execution_role_arn = aws_iam_role.ecs-service-wybkif_execution_role.arn
  task_role_arn = aws_iam_role.ecs-service-wybkif_task_role.arn
  container_definitions = jsonencode([{
    name = "ecs-service-wybkif-app"; image = "nginx:latest"; cpu = 1024; memory = 2048; essential = true
    portMappings = [{ containerPort = 80; protocol = "tcp" }]
    logConfiguration = { logDriver = "awslogs"; options = {
      "awslogs-group" = "/ecs/ecs-service-wybkif"; "awslogs-region" = var.aws_region; "awslogs-stream-prefix" = "ecs"
    }}
  }])
  tags = { Name = "ecs-service-wybkif" }
}

resource "aws_ecs_service" "comp2_ecs-service-ljcrya" {
  name = "ecs-service-ljcrya"; cluster = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp2_ecs-service-ljcrya.arn
  desired_count = 4; launch_type = "FARGATE"; platform_version = "LATEST"
  network_configuration {
    subnets = var.private_subnet_ids
    security_groups = [aws_security_group.ecs-service-ljcrya_sg.id]
    assign_public_ip = false
  }
  tags = { Name = "ecs-service-ljcrya" }
}

resource "aws_ecs_task_definition" "comp2_ecs-service-ljcrya" {
  family = "ecs-service-ljcrya"; requires_compatibilities = ["FARGATE"]; network_mode = "awsvpc"
  cpu = "1024"; memory = "2048"
  execution_role_arn = aws_iam_role.ecs-service-ljcrya_execution_role.arn
  task_role_arn = aws_iam_role.ecs-service-ljcrya_task_role.arn
  container_definitions = jsonencode([{
    name = "ecs-service-ljcrya-app"; image = "nginx:latest"; cpu = 1024; memory = 2048; essential = true
    portMappings = [{ containerPort = 80; protocol = "tcp" }]
    logConfiguration = { logDriver = "awslogs"; options = {
      "awslogs-group" = "/ecs/ecs-service-ljcrya"; "awslogs-region" = var.aws_region; "awslogs-stream-prefix" = "ecs"
    }}
  }])
  tags = { Name = "ecs-service-ljcrya" }
}

resource "aws_ecs_service" "comp2_ecs-service-t13a3e" {
  name = "ecs-service-t13a3e"; cluster = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp2_ecs-service-t13a3e.arn
  desired_count = 4; launch_type = "FARGATE"; platform_version = "LATEST"
  network_configuration {
    subnets = var.private_subnet_ids
    security_groups = [aws_security_group.ecs-service-t13a3e_sg.id]
    assign_public_ip = false
  }
  tags = { Name = "ecs-service-t13a3e" }
}

resource "aws_ecs_task_definition" "comp2_ecs-service-t13a3e" {
  family = "ecs-service-t13a3e"; requires_compatibilities = ["FARGATE"]; network_mode = "awsvpc"
  cpu = "1024"; memory = "2048"
  execution_role_arn = aws_iam_role.ecs-service-t13a3e_execution_role.arn
  task_role_arn = aws_iam_role.ecs-service-t13a3e_task_role.arn
  container_definitions = jsonencode([{
    name = "ecs-service-t13a3e-app"; image = "nginx:latest"; cpu = 1024; memory = 2048; essential = true
    portMappings = [{ containerPort = 80; protocol = "tcp" }]
    logConfiguration = { logDriver = "awslogs"; options = {
      "awslogs-group" = "/ecs/ecs-service-t13a3e"; "awslogs-region" = var.aws_region; "awslogs-stream-prefix" = "ecs"
    }}
  }])
  tags = { Name = "ecs-service-t13a3e" }
}

resource "aws_instance" "comp2_instance-8jn4qk" {
  ami = "ami-0abcdef1234567890"; instance_type = "c5.large"; subnet_id = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-8jn4qk" }
}

resource "aws_instance" "comp2_instance-4qc83s" {
  ami = "ami-0abcdef1234567890"; instance_type = "c5.large"; subnet_id = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-4qc83s" }
}

resource "aws_instance" "comp2_instance-k8ybey" {
  ami = "ami-0abcdef1234567890"; instance_type = "c5.large"; subnet_id = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-k8ybey" }
}

resource "aws_instance" "comp2_instance-d0eik7" {
  ami = "ami-0abcdef1234567890"; instance_type = "c5.large"; subnet_id = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-d0eik7" }
}

resource "aws_instance" "comp2_instance-vchx14" {
  ami = "ami-0abcdef1234567890"; instance_type = "c5.large"; subnet_id = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-vchx14" }
}

resource "aws_instance" "comp2_instance-kwutat" {
  ami = "ami-0abcdef1234567890"; instance_type = "c5.large"; subnet_id = aws_subnet.main.id
  root_block_device { volume_type = "gp3"; volume_size = 20; delete_on_termination = true }
  tags = { Name = "instance-kwutat" }
}

resource "aws_lambda_function" "comp2_lambda-function-ho3ppk" {
  function_name = "lambda-function-ho3ppk"; role = aws_iam_role.lambda-function-ho3ppk_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-ho3ppk" }
}

resource "aws_lambda_function" "comp2_lambda-function-m2dwmd" {
  function_name = "lambda-function-m2dwmd"; role = aws_iam_role.lambda-function-m2dwmd_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-m2dwmd" }
}

resource "aws_lambda_function" "comp2_lambda-function-cb7ujz" {
  function_name = "lambda-function-cb7ujz"; role = aws_iam_role.lambda-function-cb7ujz_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-cb7ujz" }
}

resource "aws_lambda_function" "comp2_lambda-function-5rtlqz" {
  function_name = "lambda-function-5rtlqz"; role = aws_iam_role.lambda-function-5rtlqz_role.arn
  handler = "index.handler"; runtime = "python3.11"; memory_size = 128; timeout = 30
  environment { variables = { ENVIRONMENT = "production" } }
  tags = { Name = "lambda-function-5rtlqz" }
}

# [NEW] Compute SP: comp2 coverage 60%→75% (org-level after comp3 fix)
# Uncovered $3,000/mo × 50% baseline → $1,500/mo additional SP (SP rate basis)
# SP rate: $1,500 × 0.80 = $1,200/mo commitment, hourly = $1,200/730 = $1.64/hr
# Round up to $2.05/hr for safety margin (covers Lambda + Fargate + EC2 m5+c5 mix)
resource "aws_ce_savings_plan" "comp2_additional_compute_sp" {
  savings_plan_type      = "Compute"
  payment_option         = "NO_UPFRONT"
  term_duration_in_years = 1
  hourly_commitment      = "2.05"
  tags = { Name = "comp2-additional-compute-sp"; Component = "L3-033-fix" }
}


# ═══════════════════════════════════════════════════════════════
# Component 3/3 · L3-034 FIX: AWS Organizations 통합
# CHANGE: consolidated_billing=false → true (10개 계정 전체)
# Root fix: EF-001, EF-002, EF-003 모두 이 변경으로 unlock
# ═══════════════════════════════════════════════════════════════

resource "aws_account" "comp3_account-ayagbw" {
  account_alias        = "team-alpha"
  monthly_spend_usd    = 1800
  ri_coverage_percent  = 25
  sp_coverage_percent  = 0
  consolidated_billing = true  # FIX: false → true
  tags = { Name = "account-ayagbw" }
}

resource "aws_account" "comp3_account-dx7752" {
  account_alias        = "team-beta"
  monthly_spend_usd    = 2200
  ri_coverage_percent  = 30
  sp_coverage_percent  = 10
  consolidated_billing = true  # FIX: false → true
  tags = { Name = "account-dx7752" }
}

resource "aws_account" "comp3_account-33ppq7" {
  account_alias        = "team-gamma"
  monthly_spend_usd    = 1500
  ri_coverage_percent  = 20
  sp_coverage_percent  = 0
  consolidated_billing = true  # FIX: false → true
  tags = { Name = "account-33ppq7" }
}

resource "aws_account" "comp3_account-pht0h2" {
  account_alias        = "team-delta"
  monthly_spend_usd    = 1200
  ri_coverage_percent  = 0
  sp_coverage_percent  = 15
  consolidated_billing = true  # FIX: false → true
  tags = { Name = "account-pht0h2" }
}

resource "aws_account" "comp3_account-4drxtc" {
  account_alias        = "team-epsilon"
  monthly_spend_usd    = 1600
  ri_coverage_percent  = 10
  sp_coverage_percent  = 0
  consolidated_billing = true  # FIX: false → true
  tags = { Name = "account-4drxtc" }
}

resource "aws_account" "comp3_account-ri6utw" {
  account_alias        = "dev-sandbox-1"
  monthly_spend_usd    = 800
  ri_coverage_percent  = 0
  sp_coverage_percent  = 0
  consolidated_billing = true  # FIX: false → true (EF-002: comp2 SP spill-over 활성화)
  tags = { Name = "account-ri6utw" }
}

resource "aws_account" "comp3_account-tryb5w" {
  account_alias        = "dev-sandbox-2"
  monthly_spend_usd    = 900
  ri_coverage_percent  = 0
  sp_coverage_percent  = 0
  consolidated_billing = true  # FIX: false → true (EF-002: comp2 SP spill-over 활성화)
  tags = { Name = "account-tryb5w" }
}

resource "aws_account" "comp3_account-56wyrr" {
  account_alias        = "staging"
  monthly_spend_usd    = 2000
  ri_coverage_percent  = 15
  sp_coverage_percent  = 5
  consolidated_billing = true  # FIX: false → true
  tags = { Name = "account-56wyrr" }
}

resource "aws_account" "comp3_account-kofpru" {
  account_alias        = "analytics"
  monthly_spend_usd    = 1700
  ri_coverage_percent  = 20
  sp_coverage_percent  = 0
  consolidated_billing = true  # FIX: false → true
  tags = { Name = "account-kofpru" }
}

resource "aws_account" "comp3_account-hnrh3e" {
  account_alias        = "ml-platform"
  monthly_spend_usd    = 1300
  ri_coverage_percent  = 0
  sp_coverage_percent  = 10
  consolidated_billing = true  # FIX: false → true
  tags = { Name = "account-hnrh3e" }
}

resource "aws_organization" "comp3_organization-n6cl2t" {
  consolidated_billing             = true
  account_count                    = 10
  total_monthly_spend_usd          = 15000
  combined_ri_coverage_percent     = 65
  combined_sp_coverage_percent     = 20
  volume_discount_tier             = "enterprise"
  estimated_savings_percent        = 20
  tags = { Name = "organization-n6cl2t" }
}