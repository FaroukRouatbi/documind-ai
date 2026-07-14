# --- Trust policy: allows ECS to assume both roles below ---

data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# --- ECS task execution role (used by the ECS agent: pull images, log, inject secrets) ---

resource "aws_iam_role" "ecs_execution" {
  name               = "documind-ai-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# --- ECS task role (used by your application code at runtime) ---

resource "aws_iam_role" "ecs_task" {
  name               = "documind-ai-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "task_permissions" {
  statement {
    sid = "DocumentsBucketAccess"

    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]

    resources = [
      "${var.documents_bucket_arn}/*"
    ]
  }

  statement {
    sid = "BedrockAccess"

    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"
    ]

    # TODO: narrow to specific model ARNs once Titan Embeddings V2 / Claude model IDs are finalized
    resources = ["*"]
  }

  statement {
    sid = "SecretsAccess"

    actions = [
      "secretsmanager:GetSecretValue"
    ]

    resources = [var.db_secret_arn]
  }
}

resource "aws_iam_policy" "task_policy" {
  name   = "documind-ai-ecs-task-permissions"
  policy = data.aws_iam_policy_document.task_permissions.json
}

resource "aws_iam_role_policy_attachment" "task_attach" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.task_policy.arn
}