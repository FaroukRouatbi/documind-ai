resource "aws_lb" "main" {
  name               = "documind-ai-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"

  subnets         = var.public_subnet_ids
  security_groups = [var.alb_security_group_id]

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "api" {
  name        = "documind-ai-api-tg-${var.environment}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/documind-ai-api-${var.environment}"
  retention_in_days = 14

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

data "aws_region" "current" {}

resource "aws_ecs_task_definition" "api" {
  family                   = "documind-ai-api-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name  = "api"
      image = "${var.api_repository_url}:latest"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "DOCUMENTS_BUCKET_NAME", value = var.documents_bucket_name },
        { name = "REDIS_ENDPOINT", value = var.redis_endpoint },
        { name = "SQS_QUEUE_URL", value = var.sqs_queue_url },
        { name = "COGNITO_USER_POOL_ID", value = var.cognito_user_pool_id },
        { name = "COGNITO_USER_POOL_CLIENT_ID", value = var.cognito_user_pool_client_id }
      ]

      secrets = [
        { name = "DB_CREDENTIALS", valueFrom = var.db_secret_arn }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = data.aws_region.current.region
          awslogs-stream-prefix = "api"
        }
      }
    }
  ])

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/documind-ai-worker-${var.environment}"
  retention_in_days = 14

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "documind-ai-worker-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name  = "worker"
      image = "${var.worker_repository_url}:latest"

      secrets = [
        { name = "DB_CREDENTIALS", valueFrom = var.db_secret_arn }
      ]

      environment = [
        { name = "DOCUMENTS_BUCKET_NAME", value = var.documents_bucket_name },
        { name = "REDIS_ENDPOINT", value = var.redis_endpoint },
        { name = "SQS_QUEUE_URL", value = var.sqs_queue_url }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker.name
          awslogs-region        = data.aws_region.current.region
          awslogs-stream-prefix = "worker"
        }
      }
    }
  ])

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_ecs_cluster" "main" {
  name = "documind-ai-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_ecs_service" "api" {
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  name            = "documind-ai-api-${var.environment}"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_ecs_service" "worker" {
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  name            = "documind-ai-worker-${var.environment}"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  tags = {
    Project     = "documoond-ai"
    Environment = var.environment
  }
}