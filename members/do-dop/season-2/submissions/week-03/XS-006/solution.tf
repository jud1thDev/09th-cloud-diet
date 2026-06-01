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

  default_tags {
    tags = {
      Env        = "production"
      Service    = "fincore-api"
      Owner      = "platform"
      CostCenter = "finops"
    }
  }
}


# Component 1/3 - L2-014: Lambda memory overprovisioning

resource "aws_lambda_function" "comp1_lambda-function-xoq9qq" {
  function_name = "lambda-function-xoq9qq"
  role          = aws_iam_role.lambda-function-xoq9qq_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"

  # P95 memory is ~100MB. Keep 512MB headroom instead of 3008MB.
  memory_size = 512
  timeout     = 30

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }

  tags = {
    Name = "lambda-function-xoq9qq"
  }
}

resource "aws_lambda_function" "comp1_lambda-function-0n5puy" {
  function_name = "lambda-function-0n5puy"
  role          = aws_iam_role.lambda-function-0n5puy_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"

  # P95 memory is ~100MB. Keep 512MB headroom instead of 3008MB.
  memory_size = 512
  timeout     = 30

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }

  tags = {
    Name = "lambda-function-0n5puy"
  }
}

resource "aws_lambda_function" "comp1_lambda-function-j5dyhj" {
  function_name = "lambda-function-j5dyhj"
  role          = aws_iam_role.lambda-function-j5dyhj_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"

  # P95 memory is ~100MB. Keep 512MB headroom instead of 3008MB.
  memory_size = 512
  timeout     = 30

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }

  tags = {
    Name = "lambda-function-j5dyhj"
  }
}

resource "aws_lambda_function" "comp1_lambda-function-v3uzlk" {
  function_name = "lambda-function-v3uzlk"
  role          = aws_iam_role.lambda-function-v3uzlk_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"

  memory_size = 512
  timeout     = 30

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }

  tags = {
    Name = "lambda-function-v3uzlk"
  }
}

resource "aws_lambda_function" "comp1_lambda-function-87jhv8" {
  function_name = "lambda-function-87jhv8"
  role          = aws_iam_role.lambda-function-87jhv8_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"

  memory_size = 512
  timeout     = 30

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }

  tags = {
    Name = "lambda-function-87jhv8"
  }
}


# Component 2/3 - L2-015: Lambda timeout overprovisioning

resource "aws_lambda_function" "comp2_lambda-function-w8lsz8" {
  function_name = "lambda-function-w8lsz8"
  role          = aws_iam_role.lambda-function-w8lsz8_role.arn
  handler       = "index.handler"
  runtime       = "nodejs18.x"

  memory_size = 1024
  # P99 is ~6.3s. Reduce timeout from 900s to 10s to cap failed-request cost.
  timeout = 10

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }

  tags = {
    Name = "lambda-function-w8lsz8"
  }
}

resource "aws_lambda_function" "comp2_lambda-function-bybdc5" {
  function_name = "lambda-function-bybdc5"
  role          = aws_iam_role.lambda-function-bybdc5_role.arn
  handler       = "index.handler"
  runtime       = "nodejs18.x"

  memory_size = 1024
  # P99 is ~4.9s. Reduce timeout from 900s to 10s to cap failed-request cost.
  timeout = 10

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }

  tags = {
    Name = "lambda-function-bybdc5"
  }
}

resource "aws_lambda_function" "comp2_lambda-function-yn04ka" {
  function_name = "lambda-function-yn04ka"
  role          = aws_iam_role.lambda-function-yn04ka_role.arn
  handler       = "index.handler"
  runtime       = "nodejs18.x"

  memory_size = 1024
  timeout     = 30

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }

  tags = {
    Name = "lambda-function-yn04ka"
  }
}

resource "aws_cloudwatch_metric_alarm" "comp2_lambda-function-w8lsz8_errors" {
  alarm_name          = "lambda-function-w8lsz8-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.comp2_lambda-function-w8lsz8.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "comp2_lambda-function-bybdc5_errors" {
  alarm_name          = "lambda-function-bybdc5-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.comp2_lambda-function-bybdc5.function_name
  }
}


# Component 3/3 - L1-010: DynamoDB provisioned capacity over-allocation

resource "aws_dynamodb_table" "comp3_dynamodb-table-bh7jai" {
  name         = "dynamodb-table-bh7jai"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "id"

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "dynamodb-table-bh7jai"
  }
}

resource "aws_dynamodb_table" "comp3_dynamodb-table-1ziky1" {
  name         = "dynamodb-table-1ziky1"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "id"

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "dynamodb-table-1ziky1"
  }
}