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
# Component 1/3 · seeded from L2-016
# ═══════════════════════════════════════════════════════════════

resource "aws_ecs_service" "comp1_ecs-service-nn78pg" {
  name            = "ecs-service-nn78pg"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-nn78pg.arn
  desired_count   = 5
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-nn78pg_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-nn78pg"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-nn78pg" {
  family                   = "ecs-service-nn78pg"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-nn78pg_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-nn78pg_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-nn78pg-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-nn78pg"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-nn78pg"
  }
}

resource "aws_ecs_service" "comp1_ecs-service-8xflm6" {
  name            = "ecs-service-8xflm6"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-8xflm6.arn
  desired_count   = 5
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-8xflm6_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-8xflm6"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-8xflm6" {
  family                   = "ecs-service-8xflm6"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-8xflm6_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-8xflm6_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-8xflm6-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-8xflm6"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-8xflm6"
  }
}

resource "aws_ecs_service" "comp1_ecs-service-od0riz" {
  name            = "ecs-service-od0riz"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-od0riz.arn
  desired_count   = 5
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-od0riz_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-od0riz"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-od0riz" {
  family                   = "ecs-service-od0riz"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-od0riz_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-od0riz_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-od0riz-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-od0riz"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-od0riz"
  }
}

resource "aws_ecs_service" "comp1_ecs-service-j53xy4" {
  name            = "ecs-service-j53xy4"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-j53xy4.arn
  desired_count   = 5
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-j53xy4_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-j53xy4"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-j53xy4" {
  family                   = "ecs-service-j53xy4"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-j53xy4_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-j53xy4_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-j53xy4-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-j53xy4"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-j53xy4"
  }
}

resource "aws_ecs_service" "comp1_ecs-service-pc94tv" {
  name            = "ecs-service-pc94tv"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-pc94tv.arn
  desired_count   = 5
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-pc94tv_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-pc94tv"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-pc94tv" {
  family                   = "ecs-service-pc94tv"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-pc94tv_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-pc94tv_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-pc94tv-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-pc94tv"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-pc94tv"
  }
}

resource "aws_ecs_service" "comp1_ecs-service-ovebd2" {
  name            = "ecs-service-ovebd2"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-ovebd2.arn
  desired_count   = 5
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-ovebd2_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-ovebd2"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-ovebd2" {
  family                   = "ecs-service-ovebd2"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-ovebd2_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-ovebd2_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-ovebd2-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-ovebd2"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-ovebd2"
  }
}

resource "aws_ecs_service" "comp1_ecs-service-4j62j6" {
  name            = "ecs-service-4j62j6"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-4j62j6.arn
  desired_count   = 5
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-4j62j6_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-4j62j6"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-4j62j6" {
  family                   = "ecs-service-4j62j6"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-4j62j6_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-4j62j6_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-4j62j6-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-4j62j6"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-4j62j6"
  }
}

resource "aws_ecs_service" "comp1_ecs-service-p0neou" {
  name            = "ecs-service-p0neou"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-p0neou.arn
  desired_count   = 5
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-p0neou_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-p0neou"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-p0neou" {
  family                   = "ecs-service-p0neou"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-p0neou_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-p0neou_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-p0neou-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-p0neou"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-p0neou"
  }
}

resource "aws_ecs_service" "comp1_ecs-service-a6kruc" {
  name            = "ecs-service-a6kruc"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-a6kruc.arn
  desired_count   = 5
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-a6kruc_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-a6kruc"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-a6kruc" {
  family                   = "ecs-service-a6kruc"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-a6kruc_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-a6kruc_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-a6kruc-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-a6kruc"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-a6kruc"
  }
}

resource "aws_ecs_service" "comp1_ecs-service-c6vk4q" {
  name            = "ecs-service-c6vk4q"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-c6vk4q.arn
  desired_count   = 5
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-c6vk4q_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-c6vk4q"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-c6vk4q" {
  family                   = "ecs-service-c6vk4q"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-c6vk4q_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-c6vk4q_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-c6vk4q-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-c6vk4q"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-c6vk4q"
  }
}

resource "aws_ecs_service" "comp1_ecs-service-9i0gu6" {
  name            = "ecs-service-9i0gu6"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-9i0gu6.arn
  desired_count   = 3
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-9i0gu6_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-9i0gu6"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-9i0gu6" {
  family                   = "ecs-service-9i0gu6"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-9i0gu6_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-9i0gu6_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-9i0gu6-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-9i0gu6"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-9i0gu6"
  }
}

resource "aws_ecs_service" "comp1_ecs-service-g1m7ei" {
  name            = "ecs-service-g1m7ei"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.comp1_ecs-service-g1m7ei.arn
  desired_count   = 3
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs-service-g1m7ei_sg.id]
    assign_public_ip = false
  }

  tags = {
    Name = "ecs-service-g1m7ei"
  }
}

resource "aws_ecs_task_definition" "comp1_ecs-service-g1m7ei" {
  family                   = "ecs-service-g1m7ei"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs-service-g1m7ei_execution_role.arn
  task_role_arn            = aws_iam_role.ecs-service-g1m7ei_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "ecs-service-g1m7ei-app"
      image     = "nginx:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ecs-service-g1m7ei"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "ecs-service-g1m7ei"
  }
}

# ═══════════════════════════════════════════════════════════════
# Component 2/3 · seeded from L1-005
# ═══════════════════════════════════════════════════════════════

resource "aws_lb" "comp2_lb-mhvy4k" {
  name               = "lb-mhvy4k"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb-mhvy4k_sg.id]
  subnets = var.public_subnet_ids

  tags = {
    Name = "lb-mhvy4k"
  }
}

# ═══════════════════════════════════════════════════════════════
# Component 3/3 · seeded from L2-017
# ═══════════════════════════════════════════════════════════════

resource "aws_autoscaling_group" "comp3_autoscaling-group-wsdeme" {
  name                = "autoscaling-group-wsdeme"
  min_size            = 2
  max_size            = 8
  desired_capacity    = 2
  vpc_zone_identifier = var.private_subnet_ids

  launch_template {
    id      = aws_launch_template.comp3_autoscaling-group-wsdeme.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "autoscaling-group-wsdeme"
    propagate_at_launch = true
  }
}

resource "aws_launch_template" "comp3_autoscaling-group-wsdeme" {
  name_prefix   = "autoscaling-group-wsdeme-"
  image_id      = "ami-0abcdef1234567890"
  instance_type = "m5.xlarge"

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "autoscaling-group-wsdeme"
    }
  }
}

resource "aws_autoscaling_policy" "comp3_autoscaling-group-wsdeme_target_tracking" {
  name                   = "autoscaling-group-wsdeme-target-tracking"
  autoscaling_group_name = aws_autoscaling_group.comp3_autoscaling-group-wsdeme.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70
  }
}

resource "aws_autoscaling_group" "comp3_autoscaling-group-85fw95" {
  name                = "autoscaling-group-85fw95"
  min_size            = 2
  max_size            = 10
  desired_capacity    = 4
  vpc_zone_identifier = var.private_subnet_ids

  launch_template {
    id      = aws_launch_template.comp3_autoscaling-group-85fw95.id
    version = "$Latest"
  }

  default_instance_warmup = 300

  tag {
    key                 = "Name"
    value               = "autoscaling-group-85fw95"
    propagate_at_launch = true
  }
}

resource "aws_launch_template" "comp3_autoscaling-group-85fw95" {
  name_prefix   = "autoscaling-group-85fw95-"
  image_id      = "ami-0abcdef1234567890"
  instance_type = "m5.xlarge"

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "autoscaling-group-85fw95"
    }
  }
}

resource "aws_autoscaling_policy" "comp3_autoscaling-group-85fw95_target_tracking" {
  name                   = "autoscaling-group-85fw95-target-tracking"
  autoscaling_group_name = aws_autoscaling_group.comp3_autoscaling-group-85fw95.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 60
  }
}